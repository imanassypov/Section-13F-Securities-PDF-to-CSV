Simple Python-based toolkit to automate retrieval of Section 13(f) securities PDF, and perform PDF to CSV data extraction.
Official List of Section 13(f) Securities is published at https://www.sec.gov/divisions/investment/13flists.htm

Installation on MacOS

1. Install brew package manager
```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

2. Install pyenv to manage Python interpreters on your machine
```
brew update
brew install pyenv
brew install pyenv-virtualenv
```

Add following lines to the bottom of your ~/.zshrc file (create a new file if one does not exist)
```
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
export PIPENV_PYTHON="$PYENV_ROOT/shims/python"

plugin=(
  pyenv
)

eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```

Load updated .zshrc file
```
source ~/.zshrc
```

3. Install Python, and activate it
```
pyenv install 3.11.0
pyenv global 3.11.0
```

4. Clone this repository to your machine
```
git clone https://github.com/imanassypov/Section-13F-Securities-PDF-to-CSV.git
```

Change directory to newly cloned repository:
```
Section-13F-Securities-PDF-to-CSV
```

5. Install required modules
```
pip install -r requirements
```

6. Execute the script
```
python sec13ftoolbox.py
Report selector not specified, looking for Current...
Scrubbing URL:	https://www.sec.gov/divisions/investment/13flists.htm
---
Current List (3rd quarter 2022): 	13flist2022q3.pdf
13flist2022q3.pdf: extracting pages:3-720
Expected row count:	24388
Extracted row count:	24388
```