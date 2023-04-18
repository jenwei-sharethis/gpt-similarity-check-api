import os
#import datetime
import openai
import json
import boto3
import botocore
import numpy as np
from openai.error import InvalidRequestError

def s3_read_file(bucket, key):
    try:
        s3Client = boto3.resource('s3')
        obj = s3Client.Object(bucket, key)
        body = obj.get()['Body'].read().decode('utf-8')
        return body
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print(f"The object {key} does not exist in {bucket}.")
            raise Exception(f"The object {key} does not exist in {bucket}.")
        else:
            print(f"Error reading file from S3: {e}")
            raise e

class GPTSimilarityCheck():
    """
    Call ChatGPT to justify if candidate articles are relevant to seed articles
    """
    def __init__(self, seed_articles,
                 format_prompt_location = ["data-science-research", "jen-wei/similarity_check/format_prompt.txt"],
                 seed_capacity = 10):
        """
        :param seed_articles: (list) List of articles as seed to compare the similarity
        :param format_prompt_location: (dict) s3 location to read format prompt file. ["bucket", "key"]
        :param seed_capacity: (int) Upper limits of number of seed articles send to ChatGPT
        """
        openai.api_key = os.environ["GPT_SECRET"]
        self.seed_articles = seed_articles[:seed_capacity]
        self.format_prompt = s3_read_file(format_prompt_location[0], format_prompt_location[1])
        self.seed_summarized_prompt = self._getGPTsummary()

    def _getGPTsummary(self, fold = 1):
        """
        Let ChatGPT summarize the common theme among seed articles
        :param num_seeds: number of seed articles to summarize
        :param fold: number of folds to split the seed articles into
        :return: response from ChatGPT
        """
        num_seeds = len(self.seed_articles)
        try:
            summary_result = ""
            fold_edge = [x for x in np.arange(num_seeds + 1, step=num_seeds * 1.0 / fold)]
            for k in range(fold):
                instruction_prompt = "Please summarize the common theme among following articles."
                content_prompt = ""
                for i in range(int(fold_edge[k]), int(fold_edge[k+1])):
                    article_text = self.seed_articles[i]["analyzed_text"]
                    content_prompt = content_prompt + f" Article {i}: " + article_text
                summary_result += self._callGPTComplete(instruction_prompt + content_prompt)
            return summary_result
        except InvalidRequestError:
            if fold >= num_seeds:
                raise Exception("Failed to summarize articles. A single article length already exceed maximum token number.")
            else:
                return self._getGPTsummary(fold=fold + 1)


    def _callGPTComplete(self, prompt):
        """
        Call the OpenAI GPT API to generate a one-time response with single request.
        Args:
            prompt (str): User input prompt.
        Returns:
            str: Generated response from the OpenAI GPT API.
        """
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user",
                       "content": prompt
                       }]
        )
        return response.choices[0].message["content"]

    def candidateRelevancy(self, candidate_articles):
        """
        Call ChatGPT to justify the relevancy of all candidate articles compared to seed articles.
        :param candidate_articles: (list) json format List of articles as condidates to let ChatGPT identify if it is relevant or discuss the same topic as seeds
        :return: (object) json list object that records responses from ChatGPT to each url
        """
        relevancy_results = []

        for i in range(len(candidate_articles)):
            candidate_text = candidate_articles[i]["analyzed_text"]
            prompt = self._loadSimilarityPrompt(candidate_text)
            response = self._cleanGPTRelevancyResponse(
                self._callGPTComplete(prompt)
            )
            response = json.loads(response)
            response["url"] = candidate_articles[i]["url"]
            relevancy_results.append(response)

        return json.loads(json.dumps(relevancy_results))

    def _loadSimilarityPrompt(self, candidate_text):
        """
        Construct prompts to ask ChatGPT if candidate article is relevant to seed articles and response in desired format.
        :param candidate_text: (str) text content of candidate article
        :return: (str) complete prompt for relevancy check
        """
        summary_prompt = "The following is the common theme from a list of articles." + self.seed_summarized_prompt
        candidate_prompt = self.format_prompt + " Candidate article: " + candidate_text

        return summary_prompt + candidate_prompt

    def _cleanGPTRelevancyResponse(self, response):
        """
        Clean up all possible additional content from ChatGPT outside brackets.
        :param response: (str) raw response from ChatGPT
        :return: cleaned up response with only brackets and content within them.
        """
        start_idx = response.find('{')
        end_idx = response.rfind('}')

        return response[start_idx:end_idx+1]

