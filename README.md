# RiotAPI: Developer Docs Parser
> v0.1.1

## Introduction
This utility allows automated scraping and parsing of Riot API developer documentation at
https://developer.riotgames.com/.
It is used mainly by https://github.com/dolejska-daniel/riot-api and all corresponding subrepositories and is primarily
meant for internal usage, though nothing is preventing anyone from using it.

## Downloading
```shell
git clone git@github.com:dolejska-daniel/riot-api-docs_parser.git
cd riot-api-docs_parser
pipenv install
```

## Usage
```shell
pipenv run python docs_parser.py --download
```

```shell
pipenv run python docs_parser.py
```
