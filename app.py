# app.py
import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
import yfinance as yf
import pandas as pd

# Dash uygulamasını başlat
app = dash.Dash(__name__)
app.title = "BIST Dashboard"

# BIST 100 sembolleri (örnek)
bist100_stocks = {
    "ASELS.IS": "Aselsan Elektronik Sanayi ve Ticaret A.Ş.",
    "THYAO.IS": "Türk Hava Yolları A.O.",
    "SISE.IS": "Şişecam A.Ş.",
    "BIMAS.IS": "BİM Birleşik Mağazalar A.Ş.",
    "EREGL.IS": "Ereğli Demir ve Çelik Fabrikaları T.A.Ş."
    # Buraya diğer BIST 100 hisseleri eklenebilir.
}

# Başlangıç verisi süresi (kullanıcı seçimi ile değiştirilecek)
def get_stock_data(ticker, period='3mo'):
    df = yf.download(ticker, period=period, interval='1d')
    df = df.dropna()
    return df

def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data):
    exp1 = data['Close'].ewm(span=12, adjust=False).mean()
    exp2 = data['Close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

app.layout = html.Div([
    html.H1("BIST 100 Hisse Dashboard", style={"textAlign": "center"}),

    html.Div([
        html.Label("Hisse Seçiniz: "),
        dcc.Dropdown(
            id='stock-selector',
            options=[{"label": name, "value": code} for code, name in bist100_stocks.items()],
            value='ASELS.IS'
        ),
        html.Br(),
        html.Label("Karşılaştırmak için ikinci hisse seçiniz (isteğe bağlı):"),
        dcc.Dropdown(
            id='compare-selector',
            options=[{"label": name, "value": code} for code, name in bist100_stocks.items()],
            placeholder="İkinci hisse seçin",
            value=None
        ),
        html.Br(),
        html.Label("Veri Aralığı: "),
        dcc.Dropdown(
            id='date-range-selector',
            options=[
                {"label": "Son 1 Ay", "value": "1mo"},
                {"label": "Son 3 Ay", "value": "3mo"},
                {"label": "Son 6 Ay", "value": "6mo"},
                {"label": "Son 1 Yıl", "value": "1y"}
            ],
            value='3mo'
        ),
        html.Br(),
        html.Label("Karanlık Mod: "),
        dcc.Checklist(
            id='dark-mode-toggle',
            options=[{"label": " Açık/Kapalı", "value": "dark"}],
            value=[]
        )
    ], style={"width": "60%", "margin": "0 auto"}),

    html.Div(id='stock-name', style={"textAlign": "center", "marginTop": "20px", "fontSize": 20}),

    html.Div([
        html.Div([
            html.H4("Fiyat Grafiği"),
            html.P("📈 Bu grafik, seçilen aralıkta günlük kapanış fiyatlarını göstermektedir."),
            dcc.Graph(id='price-chart')
        ]),

        html.Div([
            html.H4("RSI (Relative Strength Index)"),
            html.P("❓ RSI, aşırı alım ve satım bölgelerini gösterir. 70 üzeri = aşırı alım, 30 altı = aşırı satım."),
            dcc.Graph(id='rsi-chart')
        ]),

        html.Div([
            html.H4("MACD (Moving Average Convergence Divergence)"),
            html.P("📉 MACD, kısa ve uzun vadeli hareketli ortalamaların farkını gösterir. Alım-satım sinyalleri üretmek için kullanılır."),
            dcc.Graph(id='macd-chart')
        ])
    ]),

    html.Div(id='stock-info', style={"textAlign": "center", "marginTop": "20px"})
])

@app.callback(
    [Output('price-chart', 'figure'),
     Output('rsi-chart', 'figure'),
     Output('macd-chart', 'figure'),
     Output('stock-name', 'children'),
     Output('stock-info', 'children')],
    [Input('stock-selector', 'value'),
     Input('compare-selector', 'value'),
     Input('date-range-selector', 'value'),
     Input('dark-mode-toggle', 'value')]
)
def update_dashboard(stock_code, compare_code, date_range, dark_mode):
    df = get_stock_data(stock_code, date_range)
    rsi = calculate_rsi(df)
    macd, signal = calculate_macd(df)

    compare_df = get_stock_data(compare_code, date_range) if compare_code else None

    theme = "plotly_dark" if "dark" in dark_mode else "plotly_white"

    # Fiyat Grafiği
    price_fig = go.Figure()
    price_fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name=bist100_stocks[stock_code], line=dict(color='#004080')))

    if compare_df is not None:
        price_fig.add_trace(go.Scatter(x=compare_df.index, y=compare_df['Close'], mode='lines', name=bist100_stocks[compare_code], line=dict(color='orange')))

    price_fig.update_layout(
        title="Fiyat Karşılaştırması",
        xaxis_title="Tarih",
        yaxis_title="Fiyat (TL)",
        template=theme,
        height=500
    )

    # RSI Grafiği
    rsi_fig = go.Figure([
        go.Scatter(x=df.index, y=rsi, mode='lines', name='RSI', line=dict(color='orange')),
        go.Scatter(x=df.index, y=[70]*len(df), mode='lines', name='Aşırı Alım', line=dict(color='red', dash='dash')),
        go.Scatter(x=df.index, y=[30]*len(df), mode='lines', name='Aşırı Satım', line=dict(color='green', dash='dash'))
    ])
    rsi_fig.update_layout(
        title="RSI (Relative Strength Index)",
        xaxis_title="Tarih",
        yaxis_title="RSI Değeri",
        template=theme,
        height=300,
        yaxis=dict(range=[0, 100])
    )

    # MACD Grafiği
    macd_fig = go.Figure([
        go.Scatter(x=df.index, y=macd, mode='lines', name='MACD', line=dict(color='blue')),
        go.Scatter(x=df.index, y=signal, mode='lines', name='Signal', line=dict(color='red'))
    ])
    macd_fig.update_layout(
        title="MACD (Moving Average Convergence Divergence)",
        xaxis_title="Tarih",
        yaxis_title="MACD Değeri",
        template=theme,
        height=300
    )

    info = f"Son fiyat: {df['Close'][-1]:.2f} TL | Hacim: {df['Volume'][-1]:,.0f}"

    return price_fig, rsi_fig, macd_fig, bist100_stocks[stock_code], info

if __name__ == '__main__':
    app.run(debug=True)
