# NagiFlow

NagiFlow is an extensible local platform for generating AI character multimedia.

## Prerequisites

Before installing, ensure you have the following tools installed and added to your system PATH:

* **[Python 3.12+](https://www.python.org/downloads/)**
* **[Node.js 22.22.0+](https://nodejs.org/en/download)**
* **[pnpm](https://pnpm.io/installation)** (Required for frontend package management)
* **[Ollama](https://ollama.com/)** (Required for AI model inference)

## Installation

1.  Clone the repository to your local machine.
2.  Run the initialization script to set up the environment, install dependencies, and build the frontend:

    ```shell
    init.bat
    ```

    > **Note:** This script will automatically create a Python virtual environment, install backend/frontend requirements, and initialize your workspace at `%USERPROFILE%\NagiFlow`.

## Usage

Once the installation is complete, start the application using:

```shell
serve.bat
```

After the service starts, open your browser and access: [http://127.0.0.1:8000](http://127.0.0.1:8000)