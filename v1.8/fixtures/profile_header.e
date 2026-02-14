Target is mql5.ea.
Execution profile is "RAW_SPREAD".

Define m as macd_hist(close, 12, 26, 9).
Define LongSignal when m is above 0.

On each bar,
    if LongSignal,
        enter long trade with size 0.10 stop 100 points take 200 points tag "L".
