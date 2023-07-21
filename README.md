# thunkd
Simple command line tool to pull and push projects to and from Thunkable.

## Installation

Thunkd requires Python 3.8, 3.9, 3.10 or 3.11. After installing one of these version of Python, execute the command
```
pip install -r requirements.txt
```
in the top level of the repository to install the other dependencies.

## Usage

### Set Thunk token

In order to use Thunkd, you will need to configure your Thunk token. Execute the command
```
python thunkd.py set thunk_token <thunk_token>
```
where <thunk_token> is your Thunk token. See the FAQ for information on how to find your Thunk token.

### Pull

To download a project, execute the command
```
python thunkd.py pull <project_id> <file_path>
```
where <project_id> is your project ID and <file_path> is the desired output directory. See the FAQ for information on how to find the project ID.

### Push

To push to a project, execute the command
```
python thunkd.py push <project_id> <file_path>
```
where <project_id> is your project ID and <file_path> is the project directory. See the FAQ for information on how to find the project ID.

## FAQ

### How do I find my Thunk token?

The Thunk token can be found in the "https://x.thunkable.com/" cookie under the field "thunk_token". On Chrome, this can be found via the following procedure.

1. Open a Thunkable project.
2. Press F12 to open the developer console.
3. On the top bar, click on the Application tab.
4. On the side bar, click on Cookies and then "https://x.thunkable.com/".
5. Scroll to find the "thunk_token" field. The value is your Thunk token.

### How do I find my project ID?

Open your Thunkable project and examine the URL. The project ID appears after the "https://x.thunkable.com/projects/" portion of the project URL. For example, if the project URL is "https://x.thunkable.com/projects/1234567890abcdef12345678/12345678-90ab-cdef-1234-567890abcdef/designer", the project ID is "1234567890abcdef12345678".

### Why can I not see my API Keys and URLs to external sources?
After a push, some changes such as adding a Firebase API key might not be visible in the Thunkable UI. However, those values will be a part of the project as long as they are present in the JSON. It is important to test the functionality of your app frequently to address any problems as soon as they arise.
