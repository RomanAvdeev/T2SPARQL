# T2SPARQL
API + model for [Text2SPARQL Challenge](https://text2sparql.aksw.org/)

[![Typing SVG](https://readme-typing-svg.herokuapp.com?color=%2336BCF7&lines=Text+to+SPARQL)](https://git.io/typing-svg)
### Team:

api: "https://text2sparql-avdeev-roman.amvera.io/docs"

authors:

  - name: "Oleg Somov"
    affiliation: "AIRI,  MIPT"
  - name: "Daniil Berezin"
    affiliation: "MIPT"
  - name: "Roman Avdeev"
    affiliation: "MIPT"

### Source:
1) ```SPARQL.ipynb``` - notebook for testing DBpedia & Corporate graph models
2) ```for_testing``` - subsamples from QALD-9-plus / LC-QuAD2.0 for SPARQL.ipynb testing
3) ```text2sparqlAPI``` - folder with all necessary data to deploy application via FastAPI (uploaded to service [AMVERA](https://amvera.ru/))
   
   - ```/app/prod-inst.ttl``` and  ```/app/prod-vocab.ttl``` - dumps of Corporate Knowledge (Small Knowledge Graph)
     
   - ```/app/qald_9_plus_test_dbpedia```,  ```/app/qald_9_plus_train_dbpedia```  and  ```/app/train-data``` - data for RAG
   
   - ```/app/t2sparql_dbpedia_model``` and ```/app/t2sparql_corporate_model``` - models for DBpedia & Corporate knowledge graphs
     
   - ```/app/t2sparql_dbpedia_prompts``` - all prompts to ChatGPT used in DBpedia pipeline
  
   - ```/app/main.py``` - rising FastAPI with two models
  
4) ```requirements.txt``` - required libs' versions for a successful build


### Architecture
![sparql_arch](https://github.com/user-attachments/assets/3c9a783c-e3e5-4643-8a70-0c1e263c67bd)



   

