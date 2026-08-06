# Step 3B Financial Impact Summary Rules

## Primary Cards
1. Estimated Intervention Cost (central_estimate sum)
2. Estimated Financial Benefit (upper_estimate sum)
3. Estimated Net Financial Impact (net_financial_impact sum)
4. Packages Requiring Financial Input (missing_input_warning count)

## Missing Values
- Display "Requires Financial Input" or "Not Assessable"
- Never display RM0 for missing values

## Range
- Lower <= Central <= Upper displayed when all three exist

## Constraints
- Currency: RM
- No summing of incompatible periods
- No blocked ROI or payback shown
- No guaranteed savings claimed
- No scenario called optimal
- Operational urgency remains more important than financial value
