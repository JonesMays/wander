import numpy as np
import plotly.graph_objects as go
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression


'''HOW TO USE'''
# 1. Import 'from ml.py import plot_sleep_scores'
# 2. Call 'plot_sleep_scores(sleep_scores)' with a list of sleep scores
# 2.1 The list should be like this sleep_scores = [0.2, 0.5, 0.7, 0.4, 0.6, 0.8, 0.3]
# 3. The function will generate a plot and save it as 'sleep_scores.png'

def describe_sleep_score(score):
    if score < 0.3:
        return "Poor"
    elif score < 0.6:
        return "Average"
    else:
        return "Good"

def calculate_sleep_trend(sleep_scores):
    x = np.arange(len(sleep_scores))
    y = np.array(sleep_scores)
    
    # Fit a polynomial regression line to determine the trend
    poly = PolynomialFeatures(degree=2)
    X_poly = poly.fit_transform(x.reshape(-1, 1))
    model = LinearRegression()
    model.fit(X_poly, y)
    y_poly_pred = model.predict(X_poly)
    
    # Calculate the derivative of the polynomial fit to determine the trend
    trend = np.polyder(np.polyfit(x, y_poly_pred, 2))
    
    if trend[0] > 0.01:
        return "Sleep is getting better", trend[0]
    elif trend[0] < -0.01:
        return "Sleep quality is declining", trend[0]
    else:
        return "Sleep is staying constant", trend[0]

def plot_sleep_scores(sleep_scores):
    # Generate x values (e.g., days)
    x = np.arange(len(sleep_scores))
    y = np.array(sleep_scores)
    
    # Fit a polynomial regression line
    poly = PolynomialFeatures(degree=2)
    X_poly = poly.fit_transform(x.reshape(-1, 1))
    model = LinearRegression()
    model.fit(X_poly, y)
    y_poly_pred = model.predict(X_poly)
    
    # Calculate sleep trend
    trend_description, trend_rate = calculate_sleep_trend(sleep_scores)
    
    # Create a plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode='markers', name='Actual Scores'))
    fig.add_trace(go.Scatter(x=x, y=y_poly_pred, mode='lines', name='Polynomial Fit'))
    
    # Add descriptions for each score
    fig.update_layout(
        title=f'Sleep Scores: {trend_description} (Rate: {trend_rate:.2f})',
        xaxis_title='Day',
        yaxis_title='Sleep Score',
        xaxis=dict(
            tickmode='array',
            tickvals=np.arange(7),
            ticktext=['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        )
    )
    
    fig.write_image('sleep_scores.png')
    fig.show()