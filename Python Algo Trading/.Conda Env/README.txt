Python / Anaconda Environment Config with YML Files
---------------------------------------------------
To configure a python environment using anaconda we can import and export the modules and module versions being used. Environment configurations can be stored in a *.yml file. YML stands for YAML Ain't Markup Language.

To Export
---------
1. Open a terminal or Anaconda prompt.
2. Activate the environment you want to export e.g. conda activate <env_name>
3. Run the command conda env export > <env_name>.yml
4. This will create a YAML file named environment.yml in the current directory that contains all the dependencies of the environment.

To Import
---------
1. Open a terminal or Anaconda prompt.
2. Navigate to the directory where the YAML file is located.
3. Run the command conda env create -f environment.yml.
4. This will create a new environment with the same name and dependencies as the one in the YAML file.