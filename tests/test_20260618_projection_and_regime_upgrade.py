import numpy as np
import pandas as pd

from core.powerbi_path_calibration_20260617 import calibrate_projection_bundle
from core.regime_window_analytics_20260618 import build_regime_window_analytics


def market(rows=700):
    t = pd.date_range('2026-05-01', periods=rows, freq='h')
    close = 1.15 + np.arange(rows)*0.000002 + np.sin(np.arange(rows)/11)*0.0002
    open_ = np.r_[close[0], close[:-1]]
    return pd.DataFrame({'time':t,'open':open_,'high':np.maximum(open_,close)+.00018,'low':np.minimum(open_,close)-.00018,'close':close})


def paths(m, n=6):
    a=float(m.close.iloc[-1]); times=pd.date_range(m.time.iloc[-1]+pd.Timedelta(hours=1),periods=n,freq='h')
    return [pd.DataFrame({'time':times,'anchor_price':a,'path':a+np.arange(1,n+1)*step}) for step in (.00005,.00003,-.00001)]


def history(m):
    rows=[]
    end=m.time.iloc[-1]
    for p,bias in [('red',.00003),('yellow',-.00001),('blue',.00006)]:
        for h in range(1,7):
            for i in range(24):
                pred=1.15+i*.00001
                rows.append({'path':p,'horizon':h,'Predicted Close':pred,'Actual Close':pred+bias+h*.000001,'target time':end-pd.Timedelta(hours=200-i),'regime':'BULL_NORMAL'})
    return pd.DataFrame(rows)


def test_weights_bounds_and_determinism():
    m=market(); r,y,b=paths(m); hist=history(m)
    a=calibrate_projection_bundle(m,red=r,yellow=y,blue=b,horizon=6,bt_history=hist,current_regime='BULL_NORMAL')
    z=calibrate_projection_bundle(m,red=r,yellow=y,blue=b,horizon=6,bt_history=hist,current_regime='BULL_NORMAL')
    w=a['path_weights'][['red','yellow','blue']]
    assert np.allclose(w.sum(axis=1),1.0)
    assert (w >= .15-1e-9).all().all() and (w <= .55+1e-9).all().all()
    assert np.allclose(a['main'].main_path,z['main'].main_path)
    assert np.allclose(a['main'].upper_band,z['main'].upper_band)


def test_missing_path_fallbacks_and_finite_bands():
    m=market(); r,y,b=paths(m)
    for supplied in [dict(red=r,yellow=y),dict(red=r),dict()]:
        out=calibrate_projection_bundle(m,horizon=6,**supplied)
        main=out['main']
        assert np.isfinite(main[['main_path','upper_band','lower_band']]).all().all()
        assert (main.upper_band>=main.main_path).all() and (main.main_path>=main.lower_band).all()
        assert (main.band_width.diff().dropna()>=0).all()
        assert (main.main_path>0).all()
        if not supplied:
            assert np.allclose(main.main_path.to_numpy(), float(m.close.iloc[-1]))


def test_future_history_is_excluded_and_extreme_residual_is_clipped():
    m=market(); r,y,b=paths(m); hist=history(m)
    future={'path':'red','horizon':1,'Predicted Close':1.0,'Actual Close':99.0,'target time':m.time.iloc[-1]+pd.Timedelta(hours=2),'regime':'BULL_NORMAL'}
    hist2=pd.concat([hist,pd.DataFrame([future])],ignore_index=True)
    out=calibrate_projection_bundle(m,red=r,yellow=y,blue=b,horizon=6,bt_history=hist2,current_regime='BULL_NORMAL')
    assert out['summary']['error_samples']==len(hist)
    assert np.max(np.abs(np.diff(np.r_[m.close.iloc[-1],out['red'].red_path]))) <= out['summary']['atr_price']*2.01


def test_regime_windows_share_end_and_delta_is_causal():
    out=build_regime_window_analytics(market(),existing_regime='BULL_NORMAL',existing_reliability=72)
    assert out['ok']
    tables=out['tables']; ends=[]
    for key,expected in [('lower',24),('medium',120),('higher',600)]:
        row=tables[key].iloc[0]
        assert row['Actual Sample Count'] <= expected
        assert 0<=row['Regime Stability']<=100 and 0<=row['Transition Risk']<=100 and 0<=row['Reliability']<=100
        assert 0<=row['Alpha Positive Ratio']<=100 and 0<=row['Delta Positive Ratio']<=100
        assert row['Less-Risky Bias'] in {'BUY','SELL','WAIT'}
        ends.append(pd.Timestamp(row['End Time']))
    assert len(set(ends))==1
    h=out['history']
    assert np.allclose(h['delta'].dropna().to_numpy(),h['alpha'].diff().dropna().to_numpy())
