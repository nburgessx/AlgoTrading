Executive Program in Algorithmic Trading (QuantInsti)
=====================================================

**Python for Algorithmic Trading Sessions** by

Dr. Yves J. Hilpisch<br>
Adjunct Professor of Computational Finance<br>
CEO The Python Quants | The AI Machine 

Online, September 2023

Short Link
----------
http://bit.ly/epat_sep_2023

Slides & Materials
------------------

You find the introduction slides under https://certificate.tpq.io/epat.pdf

You find the materials about OOP under https://hilpisch.com/py4fi_oop_epat.html

Python Mastery in Finance Program
----------------------------------

Certificate Program in Python for Algorithmic Trading, Asset Management, and Computational Finance: https://platinum.tpq.io


Financial Theory with Python 
---------------------------------
Our newest book about Financial Theory with Python (https://home.tpq.io/books/ftwp/).

Sign up under https://finpy.pqp.io to access all the Jupyter Notebooks and execute them on our Quant Platform.

<img src="https://hilpisch.com/finpy_cover.png" width=300px border=1px>

Python for Algorithmic Trading
---------------------------------
Our recent book about Python for Algorithmic Trading (https://py4at.tpq.io).

Sign up under https://py4at.pqp.io to access all the Jupyter Notebooks and execute them on our Quant Platform.

<img src="http://hilpisch.com/pyalgo_cover_color.png" width=300px border=1px>


Python for Finance (2nd ed.)
----------------------------
Our standard reference book about Python for Finance (http://py4fi.tpq.io).

Sign up under https://py4fi.pqp.io to access all the Jupyter Notebooks and execute them on our Quant Platform.

<img src="https://hilpisch.com/images/py4fi_2nd.png" width=300px border=1px>



Further Resources
-----------------

* https://tpq.io
* https://hilpisch.com
* https://twitter.com/dyjh


Python
------

If you have either Miniconda or Anaconda already installed, there is no need to install anything new.

The code that follows uses Python 3.8. For example, download and install **Miniconda 3.8** from https://docs.conda.io/en/latest/miniconda.html if you do not have `conda` already installed.

In any case, for **Linux/Mac** you should execute the following lines on the shell  to create a new environment with the needed packages:

    conda create -n epat python=3.10
    conda activate epat
    conda install numpy pandas scikit-learn matplotlib statsmodels
    pip install cufflinks
    conda install jupyterlab
    jupyter lab

On **Windows**, execute the following lines on the Anaconda prompt:
    
    conda create -n epat python=3.10
    activate epat
    conda install numpy pandas scikit-learn matplotlib statsmodels
    pip install cufflinks
    pip install win-unicode-console
    set PYTHONIOENCODING=UTF-8
    conda install jupyterlab
    jupyter lab

Read more about the management of environments under

https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html

Docker
------

To install **Docker** see https://docs.docker.com/install/.

To run a Ubuntu-based Docker container, execute on the shell (Linux/Mac) the following: 

    docker run -ti -p 9999:9999 -h epat -v $(pwd):/root/live ubuntu:latest /bin/bash

Make sure to adjust the folder to be mounted accordingly.

ZeroMQ
------

The major resource for the `ZeroMQ` distributed messaging package based on sockets is http://zeromq.org/

Cloud
-----
Use this link to get a 100 USD bonus on **[DigitalOcean](https://m.do.co/c/fbe512dd3dac)** when signing up for a new account.


Books & Resources
-----------------

An overview of the **Python Data Model** is found under: [Python Data Model](https://docs.python.org/3/reference/datamodel.html)

Excellent book about everything important in **Python data analysis**: [Python Data Science Handbook, O'Reilly](https://learning.oreilly.com/library/view/python-data-science/9781491912126/)

Standard reference about Deep Learning with the `Keras` package (with `TensorFlow` backend): [Deep Learning with Python, Manning](https://www.manning.com/books/deep-learning-with-python)

Excellent book covering **object-oriented programming in Python**: [Fluent Python, O'Reilly, 2nd ed.](https://learning.oreilly.com/library/view/fluent-python-2nd/9781492056348/)



<img src="https://hilpisch.com/tpq_logo.png" width=250px>
