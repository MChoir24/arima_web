from statsmodels.tsa.arima_model import ARIMA

import pandas as pd
import matplotlib.pyplot as plt

def perkiraan_arima(train,test,order):
    #print('test =', test.values)
    #print(type(test))
    history = [x for x in train]
    #print(train.shape,test.shape)
    #prediksi
    prediksi = []
    for t in range(len(test)):
        model = ARIMA(history, order = order)
        model_fit = model.fit()
        output = model_fit.forecast()
        yhat = output[0][0]
        rel = max((0,yhat))
        #print('outputnya', output)
        prediksi.append(rel)
        obs = test.values[t]
        history.append(obs)
    #print('predicted=%f, expected=%f' % (rel, obs))
    return (prediksi,history)

if __name__ == '__main__':
    DATA_PATH = '/home/choir/Downloads/data_bulanan2.csv'
    produksi = pd.read_csv(DATA_PATH)
    # produksi.plot()
    # plt.show()
    train = produksi['Produksi'][:60]
    test = produksi['Produksi'][60:]
    order = (1,2,0)
    
    prediksi, history = perkiraan_arima(train=train, test=test, order=order)
    
    predic = pd.Series(prediksi)
    test2 = test.reset_index(drop=True)
    
    fig, ax = plt.subplots()
    ax.plot(test2, label="test")
    ax.plot(predic, label="prediksi")
    ax.legend()

    plt.show()