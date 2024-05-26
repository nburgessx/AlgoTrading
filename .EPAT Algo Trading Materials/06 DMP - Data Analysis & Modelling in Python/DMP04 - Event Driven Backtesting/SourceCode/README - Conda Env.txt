Prepare the EPAT Conda Environment
----------------------------------

On Windows, execute the following lines on the Anaconda prompt:

conda create -n epat python=3.10
activate epat
conda install numpy pandas scikit-learn matplotlib statsmodels
pip install cufflinks
pip install win-unicode-console
set PYTHONIOENCODING=UTF-8
conda install jupyterlab
jupyter lab