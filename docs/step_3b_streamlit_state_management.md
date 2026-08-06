# Step 3B Streamlit State Management

## Session State Keys
- executive_filters: current filter selections
- executive_data: cached authoritative datasets
- executive_data_loaded: boolean flag

## Isolation
- Executive overview state is separate from upload-session state
- Filter selections persist across interactions
- Data loaded once per session

## Performance
- Checksum-aware caching in data loader
- Pre-aggregated summaries from engines
- Limited table row counts (top-N)
