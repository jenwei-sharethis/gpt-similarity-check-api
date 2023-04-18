# gpt-similarity-check-api
This API calls ChatGPT to justify if candidate articles discuss the same event or relevant topic to seed articles

## Initialize GPTSimilarityCheck object
`param: seed_articles`: Json format dictionary with keys = ["url", "analyzed_text"]. Entries of articles as the seed for ChatGPT to extract common topic from. 

`param: format_prompt_loaction`: List in the format of [{Bucket}, {Key}]. Provide bucket and key to s3 location where the response format prompt file stored. 

`param: seed_capacity`: Int. Upper limit of seed articles that sent to ChatGPT for common topic extraction. The default number is 10.

### Functionality of format prompt
We use format prompt to ask ChatGPT responding in certain format (default is json format) and with certain keys.

The current keys are
*  `same_event`: if the candidate article discusses the same event as seeds. 1 = Ture, 0 = False
*  `relevant`: if the candidate article discusses relevant topics as seeds. 1 = Ture, 0 = False
*  `reason`: reasoning of ChatGPT making such justifications.

You can find format prompt file under `prompt` folder

## Obtain similarity check result from ChatGPT
Use `candidateRelevancy(candidate_articles)` to obtain results from ChatGPT compared to seed articles

`param: candidate_articles`: Json format dictionary. Entries of articles as candidates for ChatGPT to compare relevancy. 

`return`: Json format dictionary with keys defined in format prompt and url.
