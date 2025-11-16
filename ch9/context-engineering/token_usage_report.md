# Token Usage Measurement Report

Comparing [Yelp Navigator V1](./yelp-navigator-v1/) vs [Yelp Navigator V2](./yelp-navigator-v2/)

## Summary

- **Total V1 Tokens**: 15,536
- **Total V2 Tokens**: 3,261
- **Total Reduction**: 12,275 tokens (79.0%)
- **Average Reduction per Query**: 2455 tokens

## Cost Impact (GPT-4 Pricing)

- **V1 Cost**: $0.4661
- **V2 Cost**: $0.0978
- **Savings**: $0.3682 (79.0%)

- **Monthly Savings (10K queries)**: $3682.50

## Detailed Results

| Query                             | Detail Level   |   V1 Tokens |   V2 Tokens |   Reduction (tokens) | Reduction (%)   |
|:----------------------------------|:---------------|------------:|------------:|---------------------:|:----------------|
| Italian restaurants in Boston, MA | general        |        1050 |         555 |                  495 | 47.1%           |
| Italian restaurants in Boston, MA | detailed       |        3072 |         707 |                 2365 | 77.0%           |
| Italian restaurants in Boston, MA | reviews        |        5167 |         711 |                 4456 | 86.2%           |
| coffee shops in San Francisco, CA | general        |        1060 |         563 |                  497 | 46.9%           |
| sushi restaurants in New York, NY | reviews        |        5187 |         725 |                 4462 | 86.0%           |

