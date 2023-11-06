Running the Jupyter Notebooks
=============================
These notebooks must be run the correct order from 1-5 as indicated by their file names.
Some of the jupyter notebooks produce outputs that are needed by other notebooks.

I-Star Market Impact Model
==========================
The files implement the I-Star Market Impact Model. We use the model to to solve for optimal parameters to 
to minimize Market Impact (MI) and Timing Risk (TR) when executing and working orders. The output of the model is the I-Star i.e. optimal market impact, which determines the optimal Percentage of Market Volume (POV) to transact at. This solves the trader's dilemma, where if we trade to fast we move the market (Market Impact or MI) and if we trade to slow the market moves us (Timing Risk or TR).

The I-Star Market Impact Model looks to minimize the following,

min ( MI + Lambda * TR )

Lambda (L) indicates the investors level of risk aversion. Lambda lies in the range 0 <= L <= 3 and is the level of risk aversion determined by the investor. A high lambda is for investors wanting to trade agressively and indicates low risk aversion and a low lambda is for investors wanting to trade more passively with high risk aversion.

The model takes the following parameters:

a1 = Impact Multiplier
a2 = Order Size Parameter
a3 = Volatility Parameter
a4 = POV Parameter
b1 = % Temporary Market Impact 
(1-b1) = % Permanent Market Impact


