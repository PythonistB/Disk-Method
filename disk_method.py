import numpy as np
import sympy as sp
from dash import Dash, dcc, html, Output, Input, State, callback
import plotly.graph_objs as go
from scipy.integrate import quad
import plotly.io as pio

def volume_disk_method(func, a, b):
    volume, _ = quad(lambda x: np.pi * (func(x)**2), a, b)
    return volume

def get_plot_data(func, a, b):
    x_vals = np.linspace(a, b, 100)
    y_vals = func(x_vals)
    theta = np.linspace(0, 2 * np.pi, 100)
    X = np.linspace(a, b, 100)
    Y = np.outer(func(X), np.cos(theta))
    Z = np.outer(func(X), np.sin(theta))
    x_surface = np.repeat(X[:, np.newaxis], len(theta), axis=1)

    return x_vals, y_vals, x_surface, Y, Z

app = Dash(__name__)

app.layout = html.Div(style={'backgroundColor': '#1a1a1a', 'padding': '20px', 'color': 'yellow'}, children=[
    html.H1("Solid of Revolution Calculator"),
    dcc.Input(id='function-input', type='text', placeholder='Enter function f(x)'),
    dcc.Input(id='a-input', type='number', placeholder='Enter lower limit (a)'),
    dcc.Input(id='b-input', type='number', placeholder='Enter upper limit (b)'),
    html.Button('Calculate', id='calculate-button', n_clicks=0),
    html.Div(id='volume-output'),
    dcc.Graph(id='function-graph'),
    dcc.Graph(id='solid-graph'),
    dcc.Graph(id='solid-2d-graph')
])

pio.templates['custom'] = go.layout.Template(
    layout_paper_bgcolor='#1a1a1a',
    layout_plot_bgcolor='#1a1a1a',  # Set graph background to match the app
    layout_font_color='yellow',
    layout_font_size=12.5
)
pio.templates.default = 'plotly+custom'

@callback(
    [Output('volume-output', 'children'),
     Output('function-graph', 'figure'),
     Output('solid-graph', 'figure'),
     Output('solid-2d-graph', 'figure')],
    Input('calculate-button', 'n_clicks'),
    State('function-input', 'value'),
    State('a-input', 'value'),
    State('b-input', 'value')
)
def update_output(n_clicks, func_str, a, b):
    if n_clicks > 0:
        x = sp.symbols('x')
        func = sp.sympify(func_str)
        func_numeric = sp.lambdify(x, func, 'numpy')
        volume = volume_disk_method(func_numeric, a, b)
        x_vals, y_vals, x_surface, Y, Z = get_plot_data(func_numeric, a, b)

        function_fig = go.Figure()
        function_fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines', name='f(x)', line=dict(color='blue')))
        function_fig.add_trace(go.Scatter(x=x_vals, y=np.zeros_like(x_vals), mode='lines', name='x-axis', line=dict(color='black')))  # Continuous line
        function_fig.update_layout(title='Function f(x)', xaxis_title='x', yaxis_title='f(x)', showlegend=True)

        num_frames = 50
        frames = []

        for i in range(num_frames):
            current_theta = np.linspace(0, i / (num_frames - 1) * 2 * np.pi, 100)
            frame_y = np.outer(func_numeric(x_surface[:, 0]), np.cos(current_theta))
            frame_z = np.outer(func_numeric(x_surface[:, 0]), np.sin(current_theta))
            
            color_scale = [[0, 'green'], [1, 'rgba(255, 2, 0, 0.5)']]  # Gradient from green to red
            
            frame = go.Frame(data=[
                go.Surface(x=x_surface, y=frame_y, z=frame_z, colorscale=color_scale, opacity=0.7)
            ])
            frames.append(frame)

        final_surface = go.Surface(x=x_surface, y=Y, z=Z, colorscale='Blues', opacity=0.7)

        solid_fig = go.Figure(data=[final_surface])
        solid_fig.update_layout(title='Rotating Solid of Revolution', scene=dict(
            xaxis_title='X-axis',
            yaxis_title='Y-axis',
            zaxis_title='Z-axis'
        ))
        solid_fig.frames = frames

        solid_fig.update_layout(updatemenus=[{
            'buttons': [
                {
                    'args': [None, {'frame': {'duration': 100, 'redraw': True}, 'mode': 'immediate', 'transition': {'duration': 0}}],
                    'label': 'Play',
                    'method': 'animate'
                },
                {
                    'args': [None, {'mode': 'immediate', 'frame': {'duration': 0, 'redraw': True}}],
                    'label': 'Pause',
                    'method': 'animate'
                },
            ],
            'direction': 'down',
            'pad': {'r': 10, 't': 10},
            'showactive': True,
            'type': 'buttons',
            'x': 0.1,
            'xanchor': 'left',
            'y': 1.1,
            'yanchor': 'top'
        }])

        solid_2d_fig = go.Figure()
        solid_2d_fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines', name='f(x)', line=dict(color='blue')))
        solid_2d_fig.add_trace(go.Scatter(x=x_vals, y=np.zeros_like(x_vals), mode='lines', line=dict(color='black')))  # Continuous line

        solid_2d_fig.update_layout(title='Area Being Rotated Around X-axis', xaxis_title='x', yaxis_title='f(x)', showlegend=True)

        solid_2d_fig.add_trace(go.Scatter(
            x=np.concatenate([x_vals, x_vals[::-1]]),
            y=np.concatenate([y_vals, np.zeros_like(y_vals)]),
            fill='toself',
            fillcolor='rgba(0, 100, 255, 0.7)',
            line=dict(color='rgba(255,255,255,0)'),
            name='Area Under Curve'
        ))

        solid_2d_frames = []
        
        for i in range(num_frames):
            rotation_angle = i / (num_frames - 1) * 2 * np.pi
            
            rotated_y_vals_positive = func_numeric(x_vals) * np.cos(rotation_angle)
            rotated_y_vals_negative = -func_numeric(x_vals) * np.cos(rotation_angle)

            solid_2d_frames.append(go.Frame(data=[
                go.Scatter(x=x_vals, y=rotated_y_vals_positive, mode='lines', line=dict(color='blue')),
                go.Scatter(x=x_vals, y=rotated_y_vals_negative, mode='lines', line=dict(color='blue')),
                go.Scatter(
                    x=np.concatenate([x_vals, x_vals[::-1]]),
                    y=np.concatenate([rotated_y_vals_positive, rotated_y_vals_negative[::-1]]),
                    fill='toself',
                    fillcolor=f'rgba(0, {int(255 * i / num_frames)}, 255, 0.5)',
                    line=dict(color='rgba(255,255,255,0)'),
                    name='Filled Area'
                )
            ]))

        solid_2d_fig.frames = solid_2d_frames
        solid_2d_fig.update_layout(updatemenus=[{
            'buttons': [
                {
                    'args': [None, {'frame': {'duration': 100, 'redraw': True}, 'mode': 'immediate', 'transition': {'duration': 0}}],
                    'label': 'Play',
                    'method': 'animate'
                },
            ],
            'direction': 'down',
            'pad': {'r': 10, 't': 10},
            'showactive': True,
            'type': 'buttons',
            'x': 0.1,
            'xanchor': 'left',
            'y': 1.1,
            'yanchor': 'top'
        }])

        return f"The volume of the solid of revolution is: {volume:.4f}", function_fig, solid_fig, solid_2d_fig

    return "", go.Figure(), go.Figure(), go.Figure()

if __name__ == '__main__':
    app.run_server(debug=True)