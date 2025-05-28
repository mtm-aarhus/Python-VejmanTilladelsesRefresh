# Materielopstilling Sync Script

This Python script retrieves a JSON payload from a remote URL and synchronizes its contents into a Microsoft SQL Server table named `Materielopstilling`.

The JSON is expected to contain an array of `rows`, where each row includes:

* A unique `roadwork_id`
* Metadata such as `changedate`, `startdate`, `enddate`, `type_name`, and `the_geom`
* A field `internal_json_reference_struct`, which is a stringified JSON structure containing a `streetname` field

The script processes each row by checking whether the `roadwork_id` already exists in the database:

* If it **exists**, the row is **updated**
* If it **does not exist**, a new row is **inserted**

Before inserting or updating, the script attempts to parse the `internal_json_reference_struct` field to extract a `streetname`. If this fails or the field is missing, it defaults to `"Ikke angivet"`.

To handle transient network errors, the script retries the HTTP GET request up to **3 times**, waiting **5 minutes** between each attempt. If all retries fail, the script exits with an error.

Output is written to the console using `print()` statements. There is no function encapsulation or exception handling at the top level—the script is meant to run inside a managed runtime environment that handles logging and error capture.

---

## Installation

Install required Python packages:

```bash
pip install requests pyodbc
```

Install the ODBC driver for SQL Server:

### Ubuntu:

```bash
sudo apt install msodbcsql17
```

### Windows:

Download and install [ODBC Driver 17 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server) from Microsoft.

# Robot-Framework V3

This repo is meant to be used as a template for robots made for [OpenOrchestrator](https://github.com/itk-dev-rpa/OpenOrchestrator).

## Quick start

1. To use this template simply use this repo as a template (see [Creating a repository from a template](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template)).
__Don't__ include all branches.

2. Go to `robot_framework/__main__.py` and choose between the linear framework or queue based framework.

3. Implement all functions in the files:
    * `robot_framework/initialize.py`
    * `robot_framework/reset.py`
    * `robot_framework/process.py`

4. Change `config.py` to your needs.

5. Fill out the dependencies in the `pyproject.toml` file with all packages needed by the robot.

6. Feel free to add more files as needed. Remember that any additional python files must
be located in the folder `robot_framework` or a subfolder of it.

When the robot is run from OpenOrchestrator the `main.py` file is run which results
in the following:
1. The working directory is changed to where `main.py` is located.
2. A virtual environment is automatically setup with the required packages.
3. The framework is called passing on all arguments needed by [OpenOrchestrator](https://github.com/itk-dev-rpa/OpenOrchestrator).

## Requirements
Minimum python version 3.10

## Flow

This framework contains two different flows: A linear and a queue based.
You should only ever use one at a time. You choose which one by going into `robot_framework/__main__.py`
and uncommenting the framework you want. They are both disabled by default and an error will be
raised to remind you if you don't choose.

### Linear Flow

The linear framework is used when a robot is just going from A to Z without fetching jobs from an
OpenOrchestrator queue.
The flow of the linear framework is sketched up in the following illustration:

![Linear Flow diagram](Robot-Framework.svg)

### Queue Flow

The queue framework is used when the robot is doing multiple bite-sized tasks defined in an
OpenOrchestrator queue.
The flow of the queue framework is sketched up in the following illustration:

![Queue Flow diagram](Robot-Queue-Framework.svg)

## Linting and Github Actions

This template is also setup with flake8 and pylint linting in Github Actions.
This workflow will trigger whenever you push your code to Github.
The workflow is defined under `.github/workflows/Linting.yml`.

