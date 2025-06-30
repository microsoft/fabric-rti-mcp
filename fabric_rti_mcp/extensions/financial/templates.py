"""
KQL Templates for Financial Analytics.
"""


class FinancialKQLTemplates:
    """
    Collection of KQL query templates for financial analytics.
    """
    
    def get_moving_average_query(
        self, 
        table_name: str, 
        value_column: str, 
        time_column: str, 
        window_size: int
    ) -> str:
        """
        Generate KQL query for calculating moving average.
        
        Args:
            table_name: Name of the table
            value_column: Column containing values
            time_column: Column containing timestamps
            window_size: Size of the moving window
            
        Returns:
            str: KQL query for moving average
        """
        return f"""
{table_name}
| sort by {time_column} asc
| extend MovingAverage = series_fir({value_column}, dynamic(array_repeat(1.0/{window_size}, {window_size})), false, false)
| project {time_column}, {value_column}, MovingAverage
| where isnotnull(MovingAverage)
"""
    
    def get_trend_analysis_query(
        self, 
        table_name: str, 
        price_column: str, 
        time_column: str, 
        symbol_column: str, 
        days: int
    ) -> str:
        """
        Generate KQL query for trend analysis.
        
        Args:
            table_name: Name of the table
            price_column: Column containing prices
            time_column: Column containing timestamps
            symbol_column: Column containing symbols
            days: Number of days to analyze
            
        Returns:
            str: KQL query for trend analysis
        """
        return f"""
{table_name}
| where {time_column} >= ago({days}d)
| summarize 
    StartPrice = arg_min({time_column}, {price_column}),
    EndPrice = arg_max({time_column}, {price_column}),
    MinPrice = min({price_column}),
    MaxPrice = max({price_column}),
    AvgPrice = avg({price_column}),
    PriceVolatility = stdev({price_column})
    by {symbol_column}
| extend 
    TotalReturn = (EndPrice - StartPrice) / StartPrice * 100,
    PriceRange = MaxPrice - MinPrice,
    TrendDirection = case(
        EndPrice > StartPrice, "Upward",
        EndPrice < StartPrice, "Downward",
        "Sideways"
    )
| project 
    {symbol_column}, 
    StartPrice, 
    EndPrice, 
    TotalReturn, 
    TrendDirection, 
    MinPrice, 
    MaxPrice, 
    AvgPrice, 
    PriceVolatility, 
    PriceRange
| order by TotalReturn desc
"""
    
    def get_volatility_query(
        self, 
        table_name: str, 
        price_column: str, 
        time_column: str, 
        symbol_column: str, 
        period_days: int
    ) -> str:
        """
        Generate KQL query for volatility calculation.
        
        Args:
            table_name: Name of the table
            price_column: Column containing prices
            time_column: Column containing timestamps
            symbol_column: Column containing symbols
            period_days: Period for volatility calculation
            
        Returns:
            str: KQL query for volatility calculation
        """
        return f"""
{table_name}
| where {time_column} >= ago({period_days}d)
| sort by {symbol_column}, {time_column} asc
| serialize
| extend PrevPrice = prev({price_column}, 1)
| where isnotnull(PrevPrice)
| extend DailyReturn = ({price_column} - PrevPrice) / PrevPrice
| summarize 
    Volatility = stdev(DailyReturn) * sqrt(252), // Annualized volatility
    AvgReturn = avg(DailyReturn),
    Count = count()
    by {symbol_column}
| where Count >= 10 // Ensure sufficient data points
| project {symbol_column}, Volatility, AvgReturn, Count
| order by Volatility desc
"""
    
    def get_financial_report_query(
        self, 
        table_name: str, 
        price_column: str, 
        volume_column: str, 
        time_column: str, 
        symbol_column: str, 
        start_date: str, 
        end_date: str
    ) -> str:
        """
        Generate KQL query for comprehensive financial report.
        
        Args:
            table_name: Name of the table
            price_column: Column containing prices
            volume_column: Column containing volumes
            time_column: Column containing timestamps
            symbol_column: Column containing symbols
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            
        Returns:
            str: KQL query for financial report
        """
        return f"""
{table_name}
| where {time_column} between (datetime({start_date}) .. datetime({end_date}))
| summarize 
    OpenPrice = arg_min({time_column}, {price_column}),
    ClosePrice = arg_max({time_column}, {price_column}),
    HighPrice = max({price_column}),
    LowPrice = min({price_column}),
    AvgPrice = avg({price_column}),
    TotalVolume = sum({volume_column}),
    AvgVolume = avg({volume_column}),
    MaxVolume = max({volume_column}),
    TradingDays = dcount({time_column})
    by {symbol_column}
| extend 
    PriceChange = ClosePrice - OpenPrice,
    PriceChangePercent = (ClosePrice - OpenPrice) / OpenPrice * 100,
    PriceRange = HighPrice - LowPrice,
    VWAP = TotalVolume / TradingDays // Simplified VWAP approximation
| project 
    Symbol = {symbol_column},
    OpenPrice,
    ClosePrice,
    HighPrice,
    LowPrice,
    AvgPrice,
    PriceChange,
    PriceChangePercent,
    PriceRange,
    TotalVolume,
    AvgVolume,
    MaxVolume,
    VWAP,
    TradingDays
| order by PriceChangePercent desc
"""
    
    def get_anomaly_detection_query(
        self, 
        table_name: str, 
        price_column: str, 
        time_column: str, 
        symbol_column: str, 
        threshold_multiplier: float
    ) -> str:
        """
        Generate KQL query for price anomaly detection.
        
        Args:
            table_name: Name of the table
            price_column: Column containing prices
            time_column: Column containing timestamps
            symbol_column: Column containing symbols
            threshold_multiplier: Multiplier for standard deviation threshold
            
        Returns:
            str: KQL query for anomaly detection
        """
        return f"""
let stats = {table_name}
| summarize 
    AvgPrice = avg({price_column}),
    StdDevPrice = stdev({price_column})
    by {symbol_column};
{table_name}
| join kind=inner stats on {symbol_column}
| extend 
    ZScore = ({price_column} - AvgPrice) / StdDevPrice,
    IsAnomaly = abs({price_column} - AvgPrice) > (StdDevPrice * {threshold_multiplier})
| where IsAnomaly == true
| project 
    {time_column},
    {symbol_column},
    {price_column},
    AvgPrice,
    StdDevPrice,
    ZScore,
    Deviation = {price_column} - AvgPrice,
    DeviationPercent = ({price_column} - AvgPrice) / AvgPrice * 100
| order by abs(ZScore) desc
"""
