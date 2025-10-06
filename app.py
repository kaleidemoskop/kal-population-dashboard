import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import json

# --- 1. Daten laden und vorbereiten ---

# Dateipfade definieren
PYRAMID_DATA_PATH = 'data/pyramid_agg.csv'
AGESTATS_DATA_PATH = 'data/agestats_agg.csv'
PYRAMID_DESTATIS_PATH = 'data/pyramid_destatis.csv'
AGESTATS_DESTATIS_PATH = 'data/agestats_destatis.csv'

try:
    df_pyramid = pd.read_csv(PYRAMID_DATA_PATH)
    df_agestats = pd.read_csv(AGESTATS_DATA_PATH)
    df_pyramid_destatis = pd.read_csv(PYRAMID_DESTATIS_PATH)
    df_agestats_destatis = pd.read_csv(AGESTATS_DESTATIS_PATH)
except FileNotFoundError as e:
    print("Fehler: Mindestens eine der CSV-Dateien wurde nicht gefunden.")
    print("Bitte stelle sicher, dass folgende Dateien im Verzeichnis 'data/' vorhanden sind:")
    print(f" - {PYRAMID_DATA_PATH}")
    print(f" - {AGESTATS_DATA_PATH}")
    print(f" - {PYRAMID_DESTATIS_PATH}")
    print(f" - {AGESTATS_DESTATIS_PATH}")
    print("\nFehlermeldung:")
    print(e)
    exit()

# parameter einlesen
with open("data/simulations_meta.json") as f:
    meta_information = json.load(f)

# zugriff auf Werte
init_population = meta_information["init_population"]
sims_per_scenario = meta_information["sims_per_scenario"]
scaling_factor = meta_information["scaling_factor"]


# remove rows with age_in_years >= 100 to fit DESTATIS format
df_pyramid = df_pyramid.query("age_in_years <= 100")

# eindeutige Werte für die Steuerelemente extrahieren
available_scenarios = df_pyramid['scenario_label'].unique()
available_years = sorted(df_pyramid['simulation_year'].unique())
simulation_years = sorted(df_pyramid['simulation_year'].unique())
destatis_years = sorted(df_pyramid_destatis['simulation_year'].unique())
simulation_start_year = simulation_years[0]

# Berechne den globalen Maximalwert für eine statische Achse
global_max_val = abs(df_pyramid['count_signed']).max() * 1.1

# function to build the scenario selector
def build_scenario_selector():
    selector_style = {'display': 'flex', 'flexDirection': 'column', 'gap': '5px'}
    row_style = {'display': 'flex', 'alignItems': 'center'}
    label_style = {'width': '150px', 'fontWeight': 'bold'}
    radio_style = {'display': 'inline-block', 'margin': '0 15px'}

    return html.Div([
        # Titelzeile
        html.Div(style={'display': 'flex'}, children=[
            html.Div(style={'width': '150px'}), # Leerraum für Ausrichtung
            html.Div("niedrig", style={'flex': '1', 'textAlign': 'center'}),
            html.Div("moderat", style={'flex': '1', 'textAlign': 'center'}),
            html.Div("hoch", style={'flex': '1', 'textAlign': 'center'}),
        ]),
        # Geburtenrate
        html.Div(style=row_style, children=[
            html.Label("Geburtenhäufigkeit", style=label_style),
            dcc.RadioItems(id='g-radio', options=[{'label': ' G1', 'value': 'G1'}, {'label': ' G2', 'value': 'G2'}, {'label': ' G3', 'value': 'G3'}], value='G1', labelStyle=radio_style, style={'flex': '1', 'display': 'flex', 'justifyContent': 'space-around'})
        ]),
        # Lebenserwartung
        html.Div(style=row_style, children=[
            html.Label("Lebenserwartung", style=label_style),
            dcc.RadioItems(id='l-radio', options=[{'label': ' L1', 'value': 'L1'}, {'label': ' L2', 'value': 'L2'}, {'label': ' L3', 'value': 'L3'}], value='L1', labelStyle=radio_style, style={'flex': '1', 'display': 'flex', 'justifyContent': 'space-around'})
        ]),
        # Wanderung
        html.Div(style=row_style, children=[
            html.Label("Wanderungssaldo", style=label_style),
            dcc.RadioItems(id='w-radio', options=[{'label': ' W1', 'value': 'W1'}, {'label': ' W2', 'value': 'W2'}, {'label': ' W3', 'value': 'W3'}], value='W1', labelStyle=radio_style, style={'flex': '1', 'display': 'flex', 'justifyContent': 'space-around'})
        ]),
    ])

# --- 2. Dash-App und Layout definieren ---

app = dash.Dash(__name__)

# THIS IS THE CRITICAL LINE FOR DEPLOYMENT
server = app.server

app.layout = html.Div(style={
    'fontFamily': 'Segoe UI, sans-serif',
    'padding': '25px',
    'color': '#222',
    'fontSize': '15px',
    'lineHeight': '1.6'
}, children=[
    html.H1("Interaktives Bevölkerungs-Dashboard", style={'fontSize': '28px', 'marginBottom': '5px'}),
    html.Hr(style={'marginTop': '10px', 'marginBottom': '25px'}),

    # --- Ausgabebereich (Grafik und Tabelle) ---
    html.Div(style={'display': 'flex'}, children=[
        
        # Linke Spalte für die Pyramide und den Slider
        html.Div(style={'width': '65%', 'paddingRight': '20px'}, children=[

            # Container für Graph, Buttons, Slider
            html.Div(style={'maxWidth': '700px'}, children=[

                html.Div(
                    id='current-year-display',
                    style={
                        'fontSize': '26px',
                        'fontWeight': 'bold',
                        'textAlign': 'left',
                        'marginTop': '10px',
                        'marginBottom': '10px',
                        'color': '#333'
                    }
                ),

                # Die Bevölkerungspyramide
                dcc.Graph(
                    id='population-pyramid',
                    style={'marginTop': '20px', 'width': '100%'},
                    config={'responsive': True},
                ),

                # Button-Box mit Schatten und Abstand zum Slider
                html.Div(
                    style={
                        'display': 'flex',
                        'gap': '10px',
                        'padding': '10px',
                        'marginBottom': '20px',
                        'backgroundColor': '#f8f9fa',
                        'boxShadow': '0 2px 5px rgba(0,0,0,0.1)',
                        'borderRadius': '8px',
                        'width': 'fit-content',
                        'marginLeft': '20px',
                        'alignItems': 'center'
                    },
                    children=[
                        html.Button('▶️', id='play-button', n_clicks=0,
                                    style={'padding': '6px 12px', 'fontSize': '16px'}),
                        html.Button('⏸️', id='pause-button', n_clicks=0,
                                    style={'padding': '6px 12px', 'fontSize': '16px'})
                    ]
                ),

                # Der Slider direkt darunter
                html.Div(
                            style={
                                'backgroundColor': '#f8f9fa',
                                'boxShadow': '0 2px 5px rgba(0,0,0,0.1)',
                                'borderRadius': '8px',
                                'padding': '15px',
                                'width': '1000px',
                                'marginLeft': '20px'
                            },
                            children=[
                                dcc.Slider(
                                    id='year-slider',
                                    min=min(available_years),
                                    max=max(available_years),
                                    value=min(available_years),
                                    marks={str(year): str(year) for year in available_years if year % 10 == 0},
                                    step=1,
                                    tooltip={"placement": "bottom", "always_visible": False},
                                    updatemode='drag',
                                )
                            ]
                        ),
            ]),
        ]),

        # Rechte Spalte
        html.Div(
            style={
                'flex': '0 1 450px',
                'minWidth': '400px',
                'padding': '10px 10px 10px 20px'
            },
            children=[

                # Checkbox-Gruppe für DESTATIS + Historische Daten
                html.Div(
                    style={
                        'border': '1px solid #ccc',
                        'borderRadius': '8px',
                        'padding': '12px 16px',
                        'marginBottom': '20px',
                        'backgroundColor': '#fafafa'
                    },
                    children=[
                        html.Div([
                            html.Label("DESTATIS Benchmarking", style={'fontWeight': 'bold'}),
                            dcc.Checklist(
                                id='benchmark-toggle',
                                options=[{'label': 'Bevölkerungsberechnung einblenden', 'value': 'on'}],
                                value=[],
                                inputStyle={"marginRight": "8px"},
                                labelStyle={"display": "inline-block", "marginRight": "15px"}
                            )
                        ], style={'marginBottom': '15px'}),

                        html.Div([
                            html.Label("Historische Daten", style={'fontWeight': 'bold'}),
                            dcc.Checklist(
                                id='history-toggle',
                                options=[{'label': 'Bevölkerungsentwicklung von 1950–2021 einblenden', 'value': 'on'}],
                                value=[],
                                inputStyle={"marginRight": "8px"},
                                labelStyle={"display": "inline-block", "marginRight": "15px"}
                            )
                        ])
                    ]
                ),

                # Szenarioauswahl in eigener Box
                html.Div(
                    style={
                        'border': '1px solid #ccc',
                        'borderRadius': '8px',
                        'padding': '12px 16px',
                        'marginBottom': '25px',
                        'backgroundColor': '#fdfdfd'
                    },
                    children=[
                        html.Label("Szenario auswählen", style={'fontWeight': 'bold', 'marginBottom': '8px'}),
                        build_scenario_selector()
                    ]
                ),

                html.H4("Aggregierte Kennzahlen", style={'marginTop': '10px', 'marginBottom': '10px'}),
                html.Div(id='stats-table-container'),

                html.Div(
                    style={
                        'marginTop': '25px',
                        'padding': '15px',
                        'border': '1px solid #ddd',
                        'borderRadius': '8px',
                        'backgroundColor': '#f4f6f9',
                        'fontSize': '14px',
                        'color': '#444'
                    },
                    children=[
                        html.Strong("Methodologische Anmerkung:"),
                        html.Ul(style={'marginTop': '10px', 'paddingLeft': '20px'}, children=[
                            html.Li("27 Szenarien von DESTATIS wurden mit einem agentenbasierten Modell nachsimuliert."),
                            html.Li(f"Pro Szenario wurden {sims_per_scenario} Simulationen mit je {init_population:,} Agenten durchgeführt."),
                            html.Li("Dargestellt sind Durchschnittswerte über die jeweiligen Simulationsläufe."),
                            html.Li(f"Absolute Werte wurden zur besseren Vergleichbarkeit um den Faktor {scaling_factor:.2f} "
                                    f"auf die Bevölkerungsgröße des Jahres 2021 hochgerechnet und werden in Tausend dargestellt."
                            ),  
                        ])
                    ]
                ),
                html.Div(
                    style={
                        'marginTop': '30px',
                        'fontSize': '12px',
                        'color': '#888',
                        'textAlign': 'right'
                    },
                    children="Version 1.0 · Kaleidemoskop © 2025"
                )
            ]
        )


    ]),

    # Unsichtbares Intervall für automatische Jahr-Steuerung (wird später aktiviert)
    dcc.Interval(
        id='year-interval',
        interval=500,  # in ms (1 Sekunde)
        n_intervals=0,
        disabled=True
    )
])


# --- 3. Callback zur Aktualisierung von Grafik und Tabelle ---

@app.callback(
    Output('year-interval', 'disabled'),
    Input('play-button', 'n_clicks'),
    Input('pause-button', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_play_pause(play_clicks, pause_clicks):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'play-button':
        return False  # ▶️ → Intervall aktiv
    elif triggered_id == 'pause-button':
        return True   # ⏸️ → Intervall inaktiv

    raise dash.exceptions.PreventUpdate


@app.callback(
    Output('year-slider', 'min'),
    Output('year-slider', 'max'),
    Output('year-slider', 'marks'),
    Output('year-slider', 'value'),
    Input('benchmark-toggle', 'value'),
    Input('history-toggle', 'value'),
    Input('year-interval', 'n_intervals'),
    State('year-slider', 'value'),
    State('year-slider', 'min'),
    State('year-slider', 'max')
)
def update_year_slider(benchmark_mode, history_mode, n_intervals, current_value, slider_min, slider_max):
    benchmark_on = 'on' in (benchmark_mode or [])
    history_on = 'on' in (history_mode or [])

    # Jahrbereich setzen
    if history_on:
        years = list(range(1950, 2071))  # inkl. historische Daten
    else:
        years = list(range(simulation_start_year, 2071))

    new_min = min(years)
    new_max = max(years)
    marks = {str(year): str(year) for year in years if year % 10 == 0}

    # Jahr clampen
    if current_value is None:
        current_value = new_min
    current_value = max(min(current_value, new_max), new_min)

    # Slider automatisch weiter bewegen?
    ctx = dash.callback_context
    triggered = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    if triggered == 'year-interval':
        try:
            idx = years.index(current_value)
            next_idx = (idx + 1) % len(years)
            current_value = years[next_idx]
        except ValueError:
            current_value = new_min

    return new_min, new_max, marks, current_value


@app.callback(
    Output('current-year-display', 'children'),
    Input('year-slider', 'value')
)
def update_current_year_display(selected_year):
    if selected_year is None:
        return "Jahr wird geladen..."

    display_text = f"Jahr: {selected_year}"
    if selected_year < simulation_start_year:
        display_text += " (Historisch)"
    else:
        display_text += " (Simulation)"
        
    return display_text


@app.callback(
    Output('population-pyramid', 'figure'),
    [
        Input('g-radio', 'value'),
        Input('l-radio', 'value'),
        Input('w-radio', 'value'),
        Input('year-slider', 'value'),
        Input('benchmark-toggle', 'value'),
        Input('history-toggle', 'value')
    ]
)
def update_pyramid_figure(g_val, l_val, w_val, selected_year, benchmark_mode, history_mode):
    if selected_year is None:
        raise dash.exceptions.PreventUpdate

    benchmark_active = 'on' in benchmark_mode
    history_active = 'on' in history_mode
    is_historical = selected_year < simulation_start_year
    selected_scenario = f"{g_val}{l_val}{w_val}"

    # --- Leerer Plot vorbereiten ---
    fig_pyramid = go.Figure()

    # === (1) SIMULATIONSPLOT ===
    pyramid_filtered = df_pyramid[
        (df_pyramid['scenario_label'] == selected_scenario) &
        (df_pyramid['simulation_year'] == selected_year)
    ]
    for gender, color in {'male': '#6495ED', 'female': '#FF69B4'}.items():
        subset = pyramid_filtered[pyramid_filtered['gender'] == gender]
        fig_pyramid.add_bar(
            y=subset['age_in_years'],
            x=subset['count_signed'],
            orientation='h',
            name=gender,
            marker_color=color,
            legendgroup=gender,
            showlegend=True if gender == 'male' else True,
        )
    fig_pyramid.update_traces(selector=dict(name='male'), name='Männer')
    fig_pyramid.update_traces(selector=dict(name='female'), name='Frauen')

    # === (2) HISTORISCHER PLOT ===
    if history_active:
        historical_filtered = df_pyramid_destatis[
            (df_pyramid_destatis['scenario_label'] == 'Historical') &
            (df_pyramid_destatis['simulation_year'] == selected_year)
        ]

        for gender, color in {'male': "#395983", 'female': "#B24F80"}.items():
            subset = historical_filtered[historical_filtered['gender'] == gender]
            fig_pyramid.add_bar(
                y=subset['age_in_years'],
                x=subset['count_signed'],
                orientation='h',
                name=gender,
                marker=dict(color=color, opacity=0.9),
                legendgroup=gender,
                showlegend=True
            )
        fig_pyramid.update_traces(selector=dict(name='male'), name='Männer')
        fig_pyramid.update_traces(selector=dict(name='female'), name='Frauen')
        
    # === (3) BENCHMARKPLOT (DESTATIS) ===
    if benchmark_active:
        pyramid_benchmark = df_pyramid_destatis[
            (df_pyramid_destatis['scenario_label'] == selected_scenario) &
            (df_pyramid_destatis['simulation_year'] == selected_year)
        ]

        standard_colors = {'male': '#6495ED', 'female': '#FF69B4'}

        for gender in ['male', 'female']:
            subset = pyramid_benchmark[pyramid_benchmark['gender'] == gender]

            color = standard_colors[gender]
            opacity = 0.4 if is_historical else 0.3

            fig_pyramid.add_bar(
                y=subset['age_in_years'],
                x=subset['count_signed'],
                orientation='h',
                name=gender,
                marker=dict(color=color, opacity=opacity),
                legendgroup=gender,
                showlegend=False
            )

    # === LAYOUT ===
    fig_pyramid.update_layout(
        autosize=False,
        height=800,
        width=1000,
        barmode='overlay',
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(
            title='Bevölkerung (in Tausend)',
            tickformat=',.0f',
            range=[-global_max_val, global_max_val],
            tickvals=[-800, -600, -400, -200, 0, 200, 400, 600, 800],
            ticktext=['800', '600', '400', '200', '0', '200', '400', '600', '800']
        ),
        yaxis=dict(title='Alter in Jahren', dtick=10, range=[0, 100]),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.1,
            xanchor="center",
            x=0.4,
            title=None,
            traceorder="grouped",
            itemwidth=200
        ),
        legend_traceorder="grouped"
    )

    return fig_pyramid


@app.callback(
    Output('stats-table-container', 'children'),
    [Input('g-radio', 'value'),
     Input('l-radio', 'value'),
     Input('w-radio', 'value'),
     Input('year-slider', 'value'),
     Input('benchmark-toggle', 'value'),
     Input('history-toggle', 'value')]
)
def update_tables(g_val, l_val, w_val, selected_year, benchmark_mode, historical_mode):
    if selected_year is None:
        raise dash.exceptions.PreventUpdate
    
    benchmark_active = 'on' in benchmark_mode
    historical_active = 'on' in historical_mode

    selected_scenario = f"{g_val}{l_val}{w_val}"
    show_sim = selected_year >= simulation_start_year 

    # Basistabelle: Simulation (falls erlaubt)
    if show_sim:
        agestats_sim = df_agestats[
            (df_agestats['scenario_label'] == selected_scenario) &
            (df_agestats['simulation_year'] == selected_year)
        ][['metric', 'value']].rename(columns={'value': 'Simulation'})
        table_df = agestats_sim
    else:
        table_df = pd.DataFrame({'metric': []})  # leeres DF für Merge später

    # DESTATIS-Daten: wenn benchmark_mode aktiv (ab 2022) oder historical_mode aktiv (<2022)
    show_destatis = (
        (benchmark_active and selected_year >= simulation_start_year) or
        (historical_active and selected_year < simulation_start_year)
    )

    if show_destatis:
        if selected_year < simulation_start_year:
            benchmark_label = 'Historical'
        else:
            benchmark_label = selected_scenario

        agestats_benchmark = df_agestats_destatis[
            (df_agestats_destatis['scenario_label'] == benchmark_label) &
            (df_agestats_destatis['simulation_year'] == selected_year)
        ][['metric', 'value']].rename(columns={'value': 'DESTATIS'})

        if not agestats_benchmark.empty:
            table_df = pd.merge(table_df, agestats_benchmark, on='metric', how='outer')

    # --- Metriken & Labels ---
    order = [
        'share_over_67', 'share_20_66', 'share_under_20', 'total_over_67',
        'total_20_66', 'total_under_20', 'old_quota', 'youth_quota', 'total_pop'
    ]
    # --- Deutsche Labels ---
    labels = {
        'share_over_67': 'Anteil >67',
        'share_20_66': 'Anteil 20–66',
        'share_under_20': 'Anteil <20',
        'total_over_67': 'Anzahl >67',
        'total_20_66': 'Anzahl 20–66',
        'total_under_20': 'Anzahl <20',
        'old_quota': 'Altenquotient',
        'youth_quota': 'Jugendquotient',
        'total_pop': 'Gesamtbevölkerung'
    }

    # --- Werte formatieren ---
    def format_value(metric, value):
        if pd.isna(value):
            return "-"
        if metric.startswith('share_') or metric in ['old_quota', 'youth_quota']:
            return f"{value * 100:.2f} %"
        else:
            return f"{int(round(value)):,}"
        
    # --- Stildefinitionen ---
    table_style = {
        'width': '100%',
        'borderCollapse': 'collapse',
        'marginBottom': '16px',
        'fontSize': '13.5px'
    }

    header_style_left = {
        'textAlign': 'left',
        'borderBottom': '2px solid #444',
        'padding': '4px 6px',
        'backgroundColor': '#f4f4f4'
    }

    header_style_center = {
        'textAlign': 'center',
        'borderBottom': '2px solid #444',
        'padding': '4px 6px',
        'backgroundColor': '#f4f4f4'
    }

    cell_style_center = {
        'padding': '3px 6px',
        'textAlign': 'center',
        'whiteSpace': 'nowrap'
    }

    cell_style_left = {
        'padding': '3px 6px',
        'textAlign': 'left',
        'whiteSpace': 'nowrap'
    }

    # --- Gruppierung der Metriken ---
    group_mapping = {
        'share': ['share_over_67', 'share_20_66', 'share_under_20'],
        'total': ['total_over_67', 'total_20_66', 'total_under_20'],
        'quota': ['old_quota', 'youth_quota'],
        'total_pop': ['total_pop']
    }

    only_benchmark = benchmark_active and selected_year < simulation_start_year
    show_sim = not only_benchmark
    show_destatis = benchmark_active
        
    # --- Dynamische Header-Zeile ---
    header_cols = [html.Th("Kennzahl", style=header_style_left)]
    if show_sim:
        header_cols.append(html.Th("Simulation", style=header_style_center))
    if show_destatis:
        header_cols.append(html.Th("DESTATIS", style=header_style_center))
    table_header = [html.Thead(html.Tr(header_cols))]

    # Tabellenzeilen mit Gruppierung
    table_rows = []
    for group_name, metrics in group_mapping.items():
        for i, metric in enumerate(metrics):
            row_data = table_df[table_df['metric'] == metric]
            if not row_data.empty:
                # Stildefinition je nach Zeile
                is_total_pop = metric == 'total_pop'
                row_style_left = {**cell_style_left}
                row_style_center = {**cell_style_center}
                if is_total_pop:
                    row_style_left['fontWeight'] = 'bold'
                    row_style_center['fontWeight'] = 'bold'

                # Zellenaufbau
                cells = [html.Td(labels.get(metric, metric), style=row_style_left)]
                if show_sim:
                    sim_val = row_data.iloc[0].get('Simulation', float('nan'))
                    cells.append(html.Td(format_value(metric, sim_val), style=row_style_center))
                if show_destatis:
                    destatis_val = row_data.iloc[0].get('DESTATIS', float('nan'))
                    cells.append(html.Td(format_value(metric, destatis_val), style=row_style_center))

                table_rows.append(html.Tr(cells))

            # Füge horizontale Linie **nach letzter Metrik** der Gruppe, außer bei letzter Gruppe
            if i == len(metrics) - 1 and group_name != 'total_pop':
                colspan = 1 + int(show_sim) + int(show_destatis)
                table_rows.append(html.Tr([
                    html.Td(html.Hr(style={
                        'border': 'none',
                        'borderTop': '1px solid #aaa',
                        'margin': '4px 0'
                    }), colSpan=colspan)
                ]))


    return html.Table(table_header + [html.Tbody(table_rows)], style=table_style)



# --- 4. App starten ---
# This block runs ONLY when you execute the script directly (e.g., python app.py)
if __name__ == '__main__':
    # The command 'app.run' is for the newer versions of Dash
    app.run(debug=True)

