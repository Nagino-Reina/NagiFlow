# NagiFlow design document

NagiFlow is an extensible local platform for generating AI character multimedia.

## Use case

* Real-time chat to a specific character
* Generate multimedia content for a specific character

## Core concepts

## Data model

Data is primarily stored in SQLite, and all files are stored in workspace folders.

## Business logic

The business logic is written in Python, based on LangChain and DeepAgents, and exposed to the frontend through FastAPI.

## User interface

The user interface is written in Vue3.