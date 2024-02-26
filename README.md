# Azure Document Intelligence Custom Template User Feedback Loop Experiment

An experiment to highlight how to mimic the capabilities of Azure AI Document Intelligence Studio template training as a means to create a user feedback loop for document processing.

The provided Sample notebook demonstrates how to implement a simple way to enable a user to draw over a document that may have been processed by Azure AI Document Intelligence to provide feedback on the quality of results by highlighting incorrect or missing information with corrections. 

The goal is to showcase how a feedback mechanism can be implemented to allow the developers of custom models in Azure AI Document Intelligence to collect feedback from users to improve the model with the ability to retrain.

> [!NOTE]
> The notebook only showcases the potential user interaction. The outputs are created as the labels JSON schema used by the Azure AI Document Intelligence service. The actual feedback processing and retraining of the model is not implemented in this sample (yet!).

## Getting Started

> [!NOTE]
> This sample comes prepared with a [Invoice_1.pdf](./pdfs/Invoice_1.pdf) file that is used to test the user feedback scenario. You can also use your own PDF files.

### Prerequisites

- Install [**Visual Studio Code**](https://code.visualstudio.com/download)
- Install [**Docker Desktop**](https://www.docker.com/products/docker-desktop)
- Install [**Remote - Containers**](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension for Visual Studio Code

### Run the sample notebook

Before running the notebook, open the project in Visual Studio Code and start the development container. This will ensure that all the necessary dependencies are installed and the environment is ready to run the notebook.

Once the development container is running, open the [**Sample.ipynb**](./Sample.ipynb) notebook and follow the instructions in the notebook to run the experiment.