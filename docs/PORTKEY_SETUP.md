# Portkey Observability Setup Guide

This guide walks you through setting up Portkey AI for monitoring your Guest Search and Topic Researcher agents using Portkey's **Model Catalog**.

## What is Portkey?

Portkey is an AI Gateway that provides observability, monitoring, and analytics for your LLM applications. It helps you track:

- **API Requests** - Every call to Claude Sonnet 4
- **Token Usage** - Input/output tokens per request
- **Costs** - Real-time cost tracking across all requests
- **Latency** - Response times and performance metrics
- **Errors** - Failed requests and error patterns
- **Metadata** - Custom tags for filtering (agent type, phase, user, etc.)

## Why Add Portkey?

With Portkey, you can answer questions like:
- How much do my weekly guest searches cost?
- Which agent phase uses the most tokens?
- What's the average response time for topic searches?
- How many tool calls does the planning phase make?
- Are there any error patterns I should investigate?

## Setup Steps

### 1. Create Portkey Account

1. Go to [https://portkey.ai](https://portkey.ai)
2. Sign up for a free account
3. Complete email verification

### 2. Get Portkey API Key

1. Log in to [https://app.portkey.ai](https://app.portkey.ai)
2. Navigate to **API Keys** in the left sidebar
3. Click **Create New API Key**
4. Give it a name (e.g., "Guest Search Production")
5. Copy the API key

### 3. Add Anthropic to Model Catalog

**Important:** Portkey now uses a Model Catalog instead of Virtual Keys.

1. In Portkey dashboard, go to **AI Providers** or **Model Catalog**
2. Click **Add Provider**
3. Select **Anthropic** from the list
4. Enter your Anthropic API key (starts with `sk-ant-...`)
5. Choose a **provider slug** (e.g., `@aitoday-anthropic` or `@my-anthropic`)
   - This slug will be used to reference your Anthropic provider in API calls
6. Click **Save** or **Add Provider**

### 4. Configure Environment Variables

Add these lines to your `.env` file:

```bash
# Portkey Observability (Optional)
PORTKEY_API_KEY=your_portkey_api_key_here

# Portkey Model Catalog Configuration
PORTKEY_PROVIDER_SLUG=@aitoday-anthropic  # Use the slug you created in step 3
PORTKEY_MODEL_NAME=claude-sonnet-4-5-20250929
```

**Notes:**
- Replace `@aitoday-anthropic` with your actual provider slug from the Model Catalog
- The model name should match the Claude model you want to use
- Keep your existing `ANTHROPIC_API_KEY` in the `.env` file as fallback

### 5. Install Dependencies

The `portkey-ai` package is already in `requirements.txt`. Install it:

```bash
pip install -r requirements.txt
```

Or install directly:

```bash
pip install portkey-ai
```

### 6. Verify Integration

Run a quick test to verify Portkey is working:

```bash
python test_adapter.py
```

You should see:

```
🔍 Portkey observability enabled (Model Catalog)
✓ Client created: AnthropicPortkeyAdapter
✓ API call successful
```

Or run the full Topic Researcher:

```bash
python topic_search.py
```

## Viewing Metrics

### Dashboard Overview

1. Log in to [https://app.portkey.ai](https://app.portkey.ai)
2. Click **Logs** in the left sidebar
3. You'll see real-time requests as they happen

### Key Metrics Available

**Request Timeline**
- See every API call with timestamp
- Filter by date range, model, status

**Token Usage**
- Input tokens (prompt + tools)
- Output tokens (assistant responses)
- Total tokens per request

**Cost Tracking**
- Cost per request
- Daily/weekly/monthly totals
- Cost breakdown by model

**Performance**
- Latency (time to first token)
- Total duration
- Tokens per second

**Error Monitoring**
- Failed requests with error messages
- Error rate over time
- Common failure patterns

## How It Works

Our integration uses an **Anthropic-compatible adapter** that:

1. Wraps Portkey's SDK to maintain Anthropic's API interface
2. Automatically converts between Anthropic and OpenAI formats
3. Routes all API calls through Portkey's gateway
4. Preserves tool calling functionality
5. Falls back to direct Anthropic SDK if Portkey is not configured

**Benefits:**
- ✅ Zero changes to existing agent code
- ✅ Backwards compatible
- ✅ Optional - toggle with environment variables
- ✅ Full tool calling support
- ✅ Automatic request/response format conversion

## Advanced Usage

### Disabling Portkey

To temporarily disable Portkey without changing code:

1. Comment out or remove `PORTKEY_API_KEY` from `.env`
2. The system will automatically fall back to direct Anthropic API calls
3. No code changes needed

### Using Different Models

To use a different Claude model:

1. Update `PORTKEY_MODEL_NAME` in `.env`:
   ```bash
   PORTKEY_MODEL_NAME=claude-3-opus-20240229
   ```

2. Ensure the model is available in your Anthropic account

### Custom Provider Slugs

If you have multiple Anthropic providers configured (e.g., dev/prod):

```bash
# Development
PORTKEY_PROVIDER_SLUG=@aitoday-anthropic-dev

# Production
PORTKEY_PROVIDER_SLUG=@aitoday-anthropic-prod
```

## Troubleshooting

### "Portkey not installed" Warning

**Problem:** You see this warning even though portkey-ai is installed

```
⚠️  Portkey not installed, falling back to standard Anthropic client
```

**Solution:**
```bash
pip install --upgrade portkey-ai
```

### No Requests Showing in Dashboard

**Possible Causes:**

1. **Provider not configured** - Ensure you added Anthropic in the Model Catalog
2. **Wrong provider slug** - Check that `PORTKEY_PROVIDER_SLUG` matches your Model Catalog slug
3. **API key incorrect** - Double-check `PORTKEY_API_KEY` in `.env`
4. **Environment not loaded** - Restart your terminal or Python process
5. **Dashboard delay** - Wait 10-30 seconds for requests to appear

### "Model not found" Error

**Problem:** Error says model not found

**Solution:**
1. Verify your provider slug is correct in `.env`
2. Check that Anthropic is properly configured in Model Catalog
3. Ensure the model name is correct (e.g., `claude-sonnet-4-5-20250929`)

### Authentication Failed

**Problem:** Requests fail with authentication error

**Solution:**
1. Verify your Anthropic API key in the Portkey Model Catalog
2. Check that your Portkey API key is valid and not expired
3. Ensure the provider slug starts with `@` (e.g., `@aitoday-anthropic`)

## Cost Estimates

Based on Claude Sonnet 4 pricing (as of 2024):
- **Input:** $3.00 per million tokens
- **Output:** $15.00 per million tokens

**Typical run costs:**

| Agent | Phase | Avg Input Tokens | Avg Output Tokens | Est. Cost |
|-------|-------|------------------|-------------------|-----------|
| Guest Finder | Planning | 2,000 | 500 | $0.01 |
| Guest Finder | Search (10 queries) | 50,000 | 5,000 | $0.23 |
| Guest Finder | Report | 8,000 | 2,000 | $0.05 |
| **Total Guest Search** | | **~60,000** | **~7,500** | **~$0.29** |
| Topic Researcher | Search | 40,000 | 4,000 | $0.18 |
| Topic Researcher | Report | 5,000 | 1,500 | $0.04 |
| **Total Topic Search** | | **~45,000** | **~5,500** | **~$0.22** |

**Note:** Costs vary based on:
- Number of search iterations
- Amount of web content fetched
- Number of candidates found
- Report complexity

## Privacy & Security

### What Data Does Portkey See?

Portkey acts as a proxy between your application and Anthropic. It can see:
- ✅ Request metadata (timestamps, token counts, model)
- ✅ API keys (stored encrypted in Model Catalog)
- ✅ Prompts and responses (for observability)

### Best Practices

1. **Use separate API keys** - Create different Portkey keys for dev/prod
2. **Rotate keys** - Regenerate API keys periodically
3. **Review logs** - Check for any sensitive data being logged
4. **Read ToS** - Review Portkey's data retention and privacy policies

### Opt-Out

If you prefer not to use Portkey:
- Simply don't set the `PORTKEY_API_KEY` environment variable
- The system will work exactly the same with direct Anthropic API calls
- No Portkey SDK will be loaded

## Model Catalog vs Virtual Keys

**Old Approach (Deprecated):**
- Virtual Keys wrapped individual provider API keys
- Required manual key management
- Less flexible for multi-provider setups

**New Approach (Model Catalog):**
- Centralized provider management
- Easy switching between providers
- Built-in load balancing and fallbacks
- Simpler configuration

Our integration uses the **new Model Catalog approach** for better maintainability.

## Resources

- **Portkey Documentation:** [https://docs.portkey.ai](https://docs.portkey.ai)
- **Model Catalog Guide:** [https://portkey.ai/docs/product/model-catalog](https://portkey.ai/docs/product/model-catalog)
- **Anthropic Pricing:** [https://www.anthropic.com/pricing](https://www.anthropic.com/pricing)
- **Support:** [https://portkey.ai/support](https://portkey.ai/support)

## Next Steps

1. ✅ Set up Portkey account and API key
2. ✅ Add Anthropic provider to Model Catalog
3. ✅ Configure environment variables in `.env`
4. ✅ Install `portkey-ai` dependency
5. ✅ Run test to verify integration
6. ✅ Explore Portkey dashboard and metrics
7. 📊 Set up cost alerts (optional)
8. 📈 Create custom dashboards (optional)

---

**Questions?** Check the troubleshooting section above or review the implementation in [src/utils/portkey_client.py](../src/utils/portkey_client.py).
