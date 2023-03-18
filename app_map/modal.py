import dash_bootstrap_components as dbc
import dash
import dash_html_components as html
from dash.dependencies import Input, Output, State

# app = dash.Dash()
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.layout = html.Div(style={'backgroundColor': 'black'}, children=[
    html.H1('This is the header',
            style={'textAlign': 'center', 'color': 'yellow', 'font-family': 'Quicksand', 'font_size': '50px'}),
    html.Div(id='div1', style={'width': '49%', 'display': 'inline-block', 'background_color': 'black'}, children=[
        dbc.Button("Open modal", id="open-sm"),
        dbc.Modal(
            [
                dbc.ModalHeader("Header"),
                dbc.ModalBody("This is the content of the modal"),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close-sm", className="ml-auto")
                ),
            ],
            id="modal-sm",
        ),
        # dcc.Graph(id='graph1', figure={'layout':layout},style={'display':'none'})
    ])])


@app.callback(
    Output("modal-sm", "is_open"),
    [Input("open-sm", "n_clicks"), Input("close-sm", "n_clicks")],
    [State("modal-sm", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


if __name__ == '__main__':
    app.run_server(debug=True)