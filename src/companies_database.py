"""
Tech Giants Company Database - 500+ companies with engineering blogs and system design topics.

Organized by category for diverse content discovery.
Includes: Traditional System Design, ML Systems, AI Infrastructure, Generative AI, and Agentic AI.
"""

TECH_COMPANIES = [
    # ==================== BIG TECH / FAANG ====================
    {
        "name": "Google",
        "urls": ["https://blog.google/technology/", "https://opensource.googleblog.com/", "https://ai.googleblog.com/"],
        "topics": ["distributed-systems", "search", "kubernetes", "spanner", "mapreduce", "tensorflow", "cloud-infrastructure", "ml-infrastructure", "llm-architecture", "generative-ai-systems", "agentic-ai-workflows", "transformer-models", "ai-safety"],
        "category": "Big Tech"
    },
    {
        "name": "Meta",
        "urls": ["https://engineering.fb.com/", "https://engineering.fb.com/category/infrastructure/", "https://ai.meta.com/blog/"],
        "topics": ["social-graph", "react", "graphql", "messenger-scale", "instagram-architecture", "ai-infrastructure", "ml-recommendation-systems", "llm-training", "generative-ai-models", "agentic-ai-frameworks", "computer-vision-systems", "ai-research-infrastructure"],
        "category": "Big Tech"
    },
    {
        "name": "Amazon",
        "urls": ["https://aws.amazon.com/blogs/architecture/", "https://aws.amazon.com/builders-library/", "https://aws.amazon.com/blogs/machine-learning/"],
        "topics": ["e-commerce-scale", "dynamodb", "s3-architecture", "lambda", "event-driven", "microservices", "ml-platform", "sagemaker-architecture", "generative-ai-services", "agentic-ai-patterns", "ai-inference-optimization", "distributed-ml-training"],
        "category": "Big Tech"
    },
    {
        "name": "Netflix",
        "urls": ["https://netflixtechblog.com/", "https://netflixtechblog.com/open-source"],
        "topics": ["microservices", "zuul-gateway", "eureka", "hystrix", "open-connect-cdn", "recommendation-system", "ml-personalization", "ai-content-optimization", "generative-ai-metadata", "distributed-ml-pipelines"],
        "category": "Big Tech"
    },
    {
        "name": "Apple",
        "urls": ["https://machinelearning.apple.com/", "https://developer.apple.com/"],
        "topics": ["privacy-first", "coreml", "distributed-computing", "icloud-architecture", "app-store-scale", "on-device-ml", "neural-engine", "ai-privacy-systems", "generative-ai-features", "edge-ai-architecture"],
        "category": "Big Tech"
    },
    {
        "name": "Microsoft",
        "urls": ["https://devblogs.microsoft.com/", "https://azure.microsoft.com/en-us/blog/", "https://blogs.microsoft.com/ai/"],
        "topics": ["azure-architecture", "kubernetes", "vs-code", "windows-kernel", "distributed-cloud", "ai-platform", "openai-integration", "generative-ai-copilot", "agentic-ai-autogen", "ml-ops-infrastructure", "responsible-ai-systems"],
        "category": "Big Tech"
    },
    {
        "name": "NVIDIA",
        "urls": ["https://developer.nvidia.com/blog/", "https://blogs.nvidia.com/"],
        "topics": ["gpu-architecture", "cuda-programming", "ai-training-clusters", "ml-inference-optimization", "generative-ai-gpus", "agentic-ai-frameworks", "distributed-deep-learning", "tensorrt-optimization", "ai-supercomputing", "neural-network-design"],
        "category": "Big Tech"
    },
    {
        "name": "ByteByteGo",
        "urls": ["https://blog.bytebytego.com/", "https://bytebytego.com/newsletter"],
        "topics": ["system-design-comparisons", "architecture-patterns", "load-balancing-strategies", "database-sharding", "caching-patterns", "microservices-vs-monolith", "api-gateway-design", "event-driven-architecture", "message-queue-comparison", "consensus-algorithms", "distributed-transactions", "rate-limiting-patterns", "service-discovery", "circuit-breaker-pattern", "database-replication", "content-delivery-networks", "reverse-proxy-patterns", "database-indexing", "system-design-interviews", "scalability-patterns", "sql-vs-nosql", "rest-vs-graphql", "push-vs-pull-systems", "synchronous-vs-asynchronous", "vertical-vs-horizontal-scaling"],
        "category": "System Design Education"
    },
    {
        "name": "System Design Primer",
        "urls": ["https://github.com/donnemartin/system-design-primer"],
        "topics": ["system-design-fundamentals", "architecture-comparisons", "scalability-principles", "distributed-systems-basics", "capacity-planning", "back-of-envelope-calculations", "design-patterns"],
        "category": "System Design Education"
    },
    {
        "name": "High Scalability",
        "urls": ["http://highscalability.com/", "http://highscalability.com/blog/"],
        "topics": ["architecture-case-studies", "system-design-analysis", "scalability-comparisons", "technology-stack-reviews", "performance-optimization", "database-comparisons", "infrastructure-patterns"],
        "category": "System Design Education"
    },
    {
        "name": "InfoQ",
        "urls": ["https://www.infoq.com/", "https://www.infoq.com/articles/"],
        "topics": ["architecture-trends", "system-design-patterns", "technology-comparisons", "engineering-best-practices", "microservices-architecture", "distributed-systems", "api-design"],
        "category": "System Design Education"
    },
    {
        "name": "The New Stack",
        "urls": ["https://thenewstack.io/"],
        "topics": ["cloud-native-architecture", "container-orchestration", "service-mesh-comparison", "serverless-patterns", "observability-systems", "infrastructure-tools"],
        "category": "System Design Education"
    },

    # ==================== AI & ML COMPANIES ====================
    {
        "name": "OpenAI",
        "urls": ["https://openai.com/blog/", "https://openai.com/research/"],
        "topics": ["llm-infrastructure", "training-systems", "api-scale", "model-serving", "gpt-architecture", "generative-ai-systems", "agentic-ai-planning", "reinforcement-learning", "ai-alignment", "multimodal-models", "ai-safety-infrastructure", "chatgpt-scale"],
        "category": "AI/ML"
    },
    {
        "name": "Anthropic",
        "urls": ["https://www.anthropic.com/", "https://www.anthropic.com/research"],
        "topics": ["constitutional-ai", "llm-architecture", "safety-systems", "alignment-research", "claude-models", "generative-ai-safety", "agentic-ai-control", "interpretability-research", "ai-governance-systems", "responsible-ai-deployment"],
        "category": "AI/ML"
    },
    {
        "name": "Stability AI",
        "urls": ["https://stability.ai/blog"],
        "topics": ["image-generation", "diffusion-models", "gpu-infrastructure", "model-distribution", "stable-diffusion-architecture", "generative-ai-models", "multimodal-generation", "open-source-ai-systems", "ai-compute-optimization"],
        "category": "AI/ML"
    },
    {
        "name": "Hugging Face",
        "urls": ["https://huggingface.co/blog"],
        "topics": ["model-hub", "transformers-architecture", "community-platform", "ml-democratization", "generative-ai-models", "agentic-ai-libraries", "inference-endpoints", "distributed-training", "ai-model-versioning", "ml-ops-tools"],
        "category": "AI/ML"
    },
    {
        "name": "Cohere",
        "urls": ["https://cohere.com/blog"],
        "topics": ["nlp-infrastructure", "text-generation", "embedding-services", "enterprise-ai", "llm-deployment", "generative-ai-api", "retrieval-augmented-generation", "agentic-ai-workflows", "multilingual-ai-systems"],
        "category": "AI/ML"
    },
    {
        "name": "Midjourney",
        "urls": ["https://www.midjourney.com/"],
        "topics": ["image-generation", "diffusion-architecture", "generative-ai-systems", "ai-creativity-tools", "multimodal-models", "ai-compute-optimization", "discord-integration", "ai-art-pipelines"],
        "category": "AI/ML"
    },
    {
        "name": "Runway",
        "urls": ["https://runwayml.com/blog/"],
        "topics": ["video-generation", "generative-ai-models", "multimodal-ai", "ai-creativity-tools", "diffusion-systems", "real-time-inference", "ai-video-editing", "generative-pipelines"],
        "category": "AI/ML"
    },
    {
        "name": "Scale AI",
        "urls": ["https://scale.com/blog"],
        "topics": ["data-labeling", "ml-training-data", "ai-infrastructure", "generative-ai-evaluation", "rlhf-systems", "agentic-ai-testing", "data-quality-pipelines", "ai-benchmarking"],
        "category": "AI/ML"
    },
    {
        "name": "LangChain",
        "urls": ["https://blog.langchain.dev/"],
        "topics": ["agentic-ai-frameworks", "llm-orchestration", "retrieval-augmented-generation", "multi-agent-systems", "tool-use-patterns", "ai-agent-architecture", "generative-ai-workflows", "prompt-engineering-systems", "agent-memory-design"],
        "category": "AI/ML"
    },
    {
        "name": "LlamaIndex",
        "urls": ["https://docs.llamaindex.ai/en/stable/"],
        "topics": ["retrieval-augmented-generation", "agentic-ai-indexing", "knowledge-graph-systems", "llm-data-connectors", "query-engines", "ai-agent-tools", "semantic-search-systems", "context-window-optimization"],
        "category": "AI/ML"
    },

    # ==================== ML INFRASTRUCTURE & PLATFORMS ====================
    {
        "name": "Weights & Biases",
        "urls": ["https://wandb.ai/site/articles"],
        "topics": ["ml-experiment-tracking", "model-registry", "training-monitoring", "ml-ops-platform", "distributed-training-systems", "ml-artifact-management", "gpu-utilization-optimization", "ml-pipeline-orchestration"],
        "category": "AI/ML"
    },
    {
        "name": "Databricks",
        "urls": ["https://www.databricks.com/blog"],
        "topics": ["lakehouse-architecture", "distributed-computing", "ml-platform", "spark-optimization", "unified-analytics", "mlflow-tracking", "generative-ai-pipelines", "distributed-model-training", "ai-data-engineering"],
        "category": "AI/ML"
    },
    {
        "name": "Snowflake",
        "urls": ["https://www.snowflake.com/blog/"],
        "topics": ["data-warehouse", "cloud-architecture", "query-optimization", "data-sharing", "ml-in-database", "ai-data-platform", "generative-ai-integration", "vector-search-systems"],
        "category": "AI/ML"
    },

    # ==================== RIDE SHARING & MOBILITY ====================
    {
        "name": "Uber",
        "urls": ["https://www.uber.com/blog/engineering/", "https://eng.uber.com/"],
        "topics": ["real-time-matching", "dispatch-system", "maps-infrastructure", "marketplace-dynamics", "payment-processing", "ml-routing-optimization", "ai-demand-forecasting", "generative-ai-customer-service", "agentic-ai-dispatch"],
        "category": "Mobility"
    },
    {
        "name": "Lyft",
        "urls": ["https://eng.lyft.com/"],
        "topics": ["ride-matching", "pricing-algorithms", "real-time-tracking", "driver-rider-platform", "ml-eta-prediction", "ai-surge-pricing", "generative-ai-support"],
        "category": "Mobility"
    },
    {
        "name": "Grab",
        "urls": ["https://engineering.grab.com/"],
        "topics": ["super-app-architecture", "ride-hailing", "payment-gateway", "southeast-asia-scale", "ml-fraud-detection", "ai-routing-systems", "generative-ai-features"],
        "category": "Mobility"
    },
    {
        "name": "Didi",
        "urls": ["https://www.didiglobal.com/news/newsDetail?type=1"],
        "topics": ["ride-dispatch", "ai-routing", "safety-systems", "large-scale-matching", "ml-demand-prediction", "autonomous-driving-systems", "generative-ai-customer-service"],
        "category": "Mobility"
    },
    {
        "name": "Bird",
        "urls": ["https://medium.com/bird-engineering"],
        "topics": ["iot-fleet-management", "real-time-tracking", "mobility-platform", "ml-demand-forecasting", "ai-route-optimization"],
        "category": "Mobility"
    },

    # ==================== E-COMMERCE & RETAIL ====================
    {
        "name": "Shopify",
        "urls": ["https://shopify.engineering/"],
        "topics": ["e-commerce-platform", "multi-tenancy", "checkout-system", "app-ecosystem"],
        "category": "E-Commerce"
    },
    {
        "name": "Alibaba",
        "urls": ["https://www.alibabatech.org/"],
        "topics": ["singles-day-scale", "distributed-database", "cloud-native", "payment-systems"],
        "category": "E-Commerce"
    },
    {
        "name": "eBay",
        "urls": ["https://tech.ebayinc.com/"],
        "topics": ["marketplace-architecture", "search-systems", "payment-processing", "scalability"],
        "category": "E-Commerce"
    },
    {
        "name": "Etsy",
        "urls": ["https://www.etsy.com/codeascraft"],
        "topics": ["marketplace-search", "recommendation-engine", "seller-tools", "scaling-handmade"],
        "category": "E-Commerce"
    },
    {
        "name": "Walmart",
        "urls": ["https://medium.com/walmartglobaltech"],
        "topics": ["retail-at-scale", "supply-chain-tech", "omnichannel-platform", "inventory-systems"],
        "category": "E-Commerce"
    },
    {
        "name": "Target",
        "urls": ["https://tech.target.com/"],
        "topics": ["retail-technology", "omnichannel", "supply-chain", "personalization"],
        "category": "E-Commerce"
    },
    {
        "name": "JD.com",
        "urls": ["https://english.jd.com/newscenter/vrjd.html"],
        "topics": ["logistics-tech", "warehouse-automation", "delivery-systems", "e-commerce-scale"],
        "category": "E-Commerce"
    },
    {
        "name": "Flipkart",
        "urls": ["https://tech.flipkart.com/"],
        "topics": ["big-billion-day", "search-relevance", "recommendation-engine", "mobile-first"],
        "category": "E-Commerce"
    },

    # ==================== SOCIAL & COMMUNICATION ====================
    {
        "name": "Twitter",
        "urls": ["https://blog.twitter.com/engineering"],
        "topics": ["timeline-architecture", "real-time-analytics", "tweet-delivery", "social-graph"],
        "category": "Social"
    },
    {
        "name": "LinkedIn",
        "urls": ["https://engineering.linkedin.com/blog"],
        "topics": ["professional-graph", "feed-ranking", "job-matching", "messaging-platform"],
        "category": "Social"
    },
    {
        "name": "Slack",
        "urls": ["https://slack.engineering/"],
        "topics": ["real-time-messaging", "search-infrastructure", "workspace-scale", "websockets"],
        "category": "Social"
    },
    {
        "name": "Discord",
        "urls": ["https://discord.com/blog"],
        "topics": ["voice-infrastructure", "chat-scaling", "gaming-platform", "real-time-communication"],
        "category": "Social"
    },
    {
        "name": "Snapchat",
        "urls": ["https://newsroom.snap.com/"],
        "topics": ["ephemeral-messaging", "ar-infrastructure", "camera-ml", "content-delivery"],
        "category": "Social"
    },
    {
        "name": "Pinterest",
        "urls": ["https://medium.com/@Pinterest_Engineering"],
        "topics": ["visual-search", "recommendation-system", "image-processing", "discovery-engine"],
        "category": "Social"
    },
    {
        "name": "Reddit",
        "urls": ["https://reddit.blog/engineering/"],
        "topics": ["community-platform", "feed-ranking", "moderation-tools", "real-time-updates"],
        "category": "Social"
    },
    {
        "name": "WhatsApp",
        "urls": ["https://engineering.fb.com/category/whatsapp/"],
        "topics": ["end-to-end-encryption", "message-delivery", "billion-users-scale", "voip-infrastructure"],
        "category": "Social"
    },
    {
        "name": "Telegram",
        "urls": ["https://telegram.org/blog"],
        "topics": ["encrypted-messaging", "distributed-infrastructure", "file-sharing", "channel-architecture"],
        "category": "Social"
    },
    {
        "name": "WeChat",
        "urls": ["https://www.tencent.com/en-us/business.html"],
        "topics": ["super-app-architecture", "payment-ecosystem", "mini-programs", "social-commerce"],
        "category": "Social"
    },

    # ==================== STREAMING & MEDIA ====================
    {
        "name": "Spotify",
        "urls": ["https://engineering.atspotify.com/"],
        "topics": ["music-recommendation", "playlist-generation", "audio-streaming", "personalization"],
        "category": "Streaming"
    },
    {
        "name": "YouTube",
        "urls": ["https://blog.youtube/tech/"],
        "topics": ["video-delivery", "recommendation-algorithm", "content-id", "live-streaming-scale"],
        "category": "Streaming"
    },
    {
        "name": "Twitch",
        "urls": ["https://blog.twitch.tv/en/"],
        "topics": ["live-streaming", "chat-infrastructure", "video-transcoding", "real-time-analytics"],
        "category": "Streaming"
    },
    {
        "name": "TikTok",
        "urls": ["https://newsroom.tiktok.com/"],
        "topics": ["video-recommendation", "content-delivery", "real-time-processing", "global-scale"],
        "category": "Streaming"
    },
    {
        "name": "Disney+",
        "urls": ["https://www.disneyplus.com/"],
        "topics": ["content-delivery", "streaming-at-scale", "personalization", "global-infrastructure"],
        "category": "Streaming"
    },
    {
        "name": "Hulu",
        "urls": ["https://medium.com/hulu-tech-blog"],
        "topics": ["video-streaming", "ad-insertion", "recommendation-engine", "multi-device"],
        "category": "Streaming"
    },
    {
        "name": "SoundCloud",
        "urls": ["https://developer.soundcloud.com/blog"],
        "topics": ["audio-processing", "streaming-infrastructure", "creator-tools", "music-discovery"],
        "category": "Streaming"
    },
    {
        "name": "Patreon",
        "urls": ["https://medium.com/patreon-engineering"],
        "topics": ["creator-economy", "payment-processing", "subscription-systems", "community-platform"],
        "category": "Streaming"
    },

    # ==================== CLOUD & INFRASTRUCTURE ====================
    {
        "name": "Cloudflare",
        "urls": ["https://blog.cloudflare.com/"],
        "topics": ["cdn-architecture", "ddos-protection", "edge-computing", "dns-infrastructure"],
        "category": "Infrastructure"
    },
    {
        "name": "DigitalOcean",
        "urls": ["https://www.digitalocean.com/blog/engineering"],
        "topics": ["cloud-infrastructure", "virtualization", "developer-tools", "managed-services"],
        "category": "Infrastructure"
    },
    {
        "name": "HashiCorp",
        "urls": ["https://www.hashicorp.com/blog"],
        "topics": ["infrastructure-as-code", "service-mesh", "secrets-management", "multi-cloud"],
        "category": "Infrastructure"
    },
    {
        "name": "MongoDB",
        "urls": ["https://www.mongodb.com/blog"],
        "topics": ["document-database", "distributed-storage", "sharding", "atlas-platform"],
        "category": "Infrastructure"
    },
    {
        "name": "Elastic",
        "urls": ["https://www.elastic.co/blog"],
        "topics": ["search-engine", "log-analytics", "distributed-indexing", "observability"],
        "category": "Infrastructure"
    },
    {
        "name": "Datadog",
        "urls": ["https://www.datadoghq.com/blog/engineering/"],
        "topics": ["monitoring-at-scale", "time-series-database", "distributed-tracing", "log-management"],
        "category": "Infrastructure"
    },
    {
        "name": "Snowflake",
        "urls": ["https://www.snowflake.com/blog/"],
        "topics": ["data-warehouse", "cloud-architecture", "query-optimization", "multi-cluster"],
        "category": "Infrastructure"
    },
    {
        "name": "Databricks",
        "urls": ["https://www.databricks.com/blog"],
        "topics": ["lakehouse-architecture", "distributed-computing", "ml-platform", "spark-optimization"],
        "category": "Infrastructure"
    },

    # ==================== PAYMENTS & FINTECH ====================
    {
        "name": "Stripe",
        "urls": ["https://stripe.com/blog/engineering"],
        "topics": ["payment-processing", "distributed-transactions", "fraud-detection", "api-design"],
        "category": "Fintech"
    },
    {
        "name": "PayPal",
        "urls": ["https://medium.com/paypal-engineering"],
        "topics": ["payment-gateway", "transaction-processing", "security-infrastructure", "global-scale"],
        "category": "Fintech"
    },
    {
        "name": "Square",
        "urls": ["https://developer.squareup.com/blog/"],
        "topics": ["point-of-sale", "payment-processing", "financial-services", "small-business-tech"],
        "category": "Fintech"
    },
    {
        "name": "Coinbase",
        "urls": ["https://blog.coinbase.com/tagged/engineering"],
        "topics": ["crypto-infrastructure", "blockchain-scale", "wallet-security", "trading-platform"],
        "category": "Fintech"
    },
    {
        "name": "Robinhood",
        "urls": ["https://robinhood.engineering/"],
        "topics": ["trading-platform", "real-time-pricing", "order-execution", "market-data"],
        "category": "Fintech"
    },
    {
        "name": "Plaid",
        "urls": ["https://medium.com/plaid-engineering"],
        "topics": ["banking-apis", "data-aggregation", "financial-infrastructure", "oauth-flows"],
        "category": "Fintech"
    },
    {
        "name": "Adyen",
        "urls": ["https://www.adyen.com/blog"],
        "topics": ["global-payments", "payment-routing", "fraud-prevention", "multi-currency"],
        "category": "Fintech"
    },
    {
        "name": "Klarna",
        "urls": ["https://developers.klarna.com/blog/"],
        "topics": ["bnpl-architecture", "credit-scoring", "checkout-optimization", "risk-management"],
        "category": "Fintech"
    },
    {
        "name": "Revolut",
        "urls": ["https://engineering.revolut.com/"],
        "topics": ["digital-banking", "multi-currency", "trading-infrastructure", "fraud-detection"],
        "category": "Fintech"
    },

    # ==================== TRAVEL & HOSPITALITY ====================
    {
        "name": "Airbnb",
        "urls": ["https://medium.com/airbnb-engineering"],
        "topics": ["booking-system", "search-ranking", "trust-platform", "pricing-algorithms"],
        "category": "Travel"
    },
    {
        "name": "Booking.com",
        "urls": ["https://booking.ai/"],
        "topics": ["hotel-search", "recommendation-system", "pricing-engine", "global-reservation"],
        "category": "Travel"
    },
    {
        "name": "Expedia",
        "urls": ["https://medium.com/expedia-group-tech"],
        "topics": ["travel-search", "booking-platform", "price-comparison", "multi-supplier"],
        "category": "Travel"
    },
    {
        "name": "TripAdvisor",
        "urls": ["https://medium.com/@TripAdvisorEngineering"],
        "topics": ["review-system", "content-moderation", "search-ranking", "recommendation-engine"],
        "category": "Travel"
    },
    {
        "name": "Skyscanner",
        "urls": ["https://medium.com/@SkyscannerEng"],
        "topics": ["flight-search", "price-aggregation", "real-time-updates", "travel-tech"],
        "category": "Travel"
    },
    {
        "name": "Uber Eats",
        "urls": ["https://eng.uber.com/category/uber-eats/"],
        "topics": ["food-delivery", "restaurant-platform", "routing-optimization", "eta-prediction"],
        "category": "Travel"
    },
    {
        "name": "DoorDash",
        "urls": ["https://doordash.engineering/"],
        "topics": ["delivery-logistics", "dispatch-algorithms", "restaurant-tech", "real-time-tracking"],
        "category": "Travel"
    },
    {
        "name": "Grubhub",
        "urls": ["https://medium.com/grubhub-engineering"],
        "topics": ["food-ordering", "delivery-routing", "restaurant-integration", "payment-processing"],
        "category": "Travel"
    },

    # ==================== DEVELOPER TOOLS ====================
    {
        "name": "GitHub",
        "urls": ["https://github.blog/engineering/"],
        "topics": ["git-infrastructure", "code-review", "ci-cd-pipeline", "collaboration-tools"],
        "category": "DevTools"
    },
    {
        "name": "GitLab",
        "urls": ["https://about.gitlab.com/blog/engineering/"],
        "topics": ["devops-platform", "ci-cd-scale", "code-review", "distributed-version-control"],
        "category": "DevTools"
    },
    {
        "name": "Vercel",
        "urls": ["https://vercel.com/blog/engineering"],
        "topics": ["edge-network", "serverless-scale", "build-optimization", "deployment-pipeline"],
        "category": "DevTools"
    },
    {
        "name": "Netlify",
        "urls": ["https://www.netlify.com/blog/"],
        "topics": ["jamstack-architecture", "cdn-deployment", "build-systems", "edge-functions"],
        "category": "DevTools"
    },
    {
        "name": "Twilio",
        "urls": ["https://www.twilio.com/blog"],
        "topics": ["communications-api", "sms-infrastructure", "voice-routing", "global-scale"],
        "category": "DevTools"
    },
    {
        "name": "Segment",
        "urls": ["https://segment.com/blog/"],
        "topics": ["data-pipeline", "event-tracking", "customer-data", "analytics-infrastructure"],
        "category": "DevTools"
    },
    {
        "name": "Sentry",
        "urls": ["https://blog.sentry.io/"],
        "topics": ["error-tracking", "performance-monitoring", "distributed-tracing", "real-time-alerts"],
        "category": "DevTools"
    },

    # ==================== SECURITY ====================
    {
        "name": "Okta",
        "urls": ["https://developer.okta.com/blog/"],
        "topics": ["authentication-systems", "identity-management", "oauth-infrastructure", "zero-trust"],
        "category": "Security"
    },
    {
        "name": "Auth0",
        "urls": ["https://auth0.com/blog/"],
        "topics": ["authentication-as-service", "jwt-architecture", "multi-tenant-security", "identity-federation"],
        "category": "Security"
    },
    {
        "name": "CrowdStrike",
        "urls": ["https://www.crowdstrike.com/blog/"],
        "topics": ["endpoint-protection", "threat-detection", "cloud-native-security", "incident-response"],
        "category": "Security"
    },
    {
        "name": "Palo Alto Networks",
        "urls": ["https://www.paloaltonetworks.com/blog/"],
        "topics": ["network-security", "firewall-architecture", "threat-intelligence", "zero-trust"],
        "category": "Security"
    },
    {
        "name": "1Password",
        "urls": ["https://1password.engineering/"],
        "topics": ["password-management", "encryption-architecture", "zero-knowledge-proofs", "secure-sync"],
        "category": "Security"
    },
    {
        "name": "LastPass",
        "urls": ["https://blog.lastpass.com/"],
        "topics": ["vault-architecture", "encryption-systems", "password-generation", "secure-sharing"],
        "category": "Security"
    },

    # ==================== GAMING ====================
    {
        "name": "Epic Games",
        "urls": ["https://dev.epicgames.com/community/"],
        "topics": ["unreal-engine", "multiplayer-infrastructure", "matchmaking", "game-engine-architecture"],
        "category": "Gaming"
    },
    {
        "name": "Riot Games",
        "urls": ["https://technology.riotgames.com/"],
        "topics": ["multiplayer-gaming", "anti-cheat-systems", "game-server-architecture", "player-matching"],
        "category": "Gaming"
    },
    {
        "name": "Blizzard",
        "urls": ["https://news.blizzard.com/"],
        "topics": ["mmo-architecture", "real-time-multiplayer", "content-delivery", "player-progression"],
        "category": "Gaming"
    },
    {
        "name": "Valve",
        "urls": ["https://partner.steamgames.com/news"],
        "topics": ["steam-platform", "game-distribution", "multiplayer-networking", "workshop-system"],
        "category": "Gaming"
    },
    {
        "name": "Unity",
        "urls": ["https://blog.unity.com/technology"],
        "topics": ["game-engine", "real-time-3d", "multiplayer-framework", "cross-platform"],
        "category": "Gaming"
    },
    {
        "name": "Roblox",
        "urls": ["https://engineering.roblox.com/"],
        "topics": ["user-generated-content", "real-time-multiplayer", "physics-engine", "creator-economy"],
        "category": "Gaming"
    },

    # ==================== HEALTHTECH ====================
    {
        "name": "23andMe",
        "urls": ["https://www.23andme.com/"],
        "topics": ["genomics-data", "dna-analysis", "privacy-first", "large-scale-processing"],
        "category": "HealthTech"
    },
    {
        "name": "Verily",
        "urls": ["https://www.verily.com/"],
        "topics": ["health-data", "clinical-trials", "ai-diagnostics", "medical-devices"],
        "category": "HealthTech"
    },
    {
        "name": "Oscar Health",
        "urls": ["https://medium.com/@OscarTech"],
        "topics": ["healthcare-platform", "insurance-tech", "claims-processing", "telemedicine"],
        "category": "HealthTech"
    },
    {
        "name": "Teladoc",
        "urls": ["https://www.teladochealth.com/"],
        "topics": ["telemedicine", "video-consultations", "healthcare-network", "patient-management"],
        "category": "HealthTech"
    },

    # ==================== EDTECH ====================
    {
        "name": "Coursera",
        "urls": ["https://medium.com/coursera-engineering"],
        "topics": ["learning-platform", "video-delivery", "assessment-system", "personalization"],
        "category": "EdTech"
    },
    {
        "name": "Khan Academy",
        "urls": ["https://blog.khanacademy.org/"],
        "topics": ["adaptive-learning", "content-delivery", "progress-tracking", "personalized-education"],
        "category": "EdTech"
    },
    {
        "name": "Duolingo",
        "urls": ["https://blog.duolingo.com/"],
        "topics": ["language-learning", "gamification", "ml-recommendation", "user-engagement"],
        "category": "EdTech"
    },
    {
        "name": "Udemy",
        "urls": ["https://medium.com/udemy-engineering"],
        "topics": ["course-platform", "video-streaming", "instructor-tools", "learning-analytics"],
        "category": "EdTech"
    },

    # ==================== AI & ML COMPANIES ====================
    {
        "name": "OpenAI",
        "urls": ["https://openai.com/blog/"],
        "topics": ["llm-infrastructure", "training-systems", "api-scale", "model-serving"],
        "category": "AI/ML"
    },
    {
        "name": "Anthropic",
        "urls": ["https://www.anthropic.com/"],
        "topics": ["constitutional-ai", "llm-architecture", "safety-systems", "alignment-research"],
        "category": "AI/ML"
    },
    {
        "name": "Stability AI",
        "urls": ["https://stability.ai/blog"],
        "topics": ["image-generation", "diffusion-models", "gpu-infrastructure", "model-distribution"],
        "category": "AI/ML"
    },
    {
        "name": "Hugging Face",
        "urls": ["https://huggingface.co/blog"],
        "topics": ["model-hub", "transformers-architecture", "community-platform", "ml-democratization"],
        "category": "AI/ML"
    },
    {
        "name": "Cohere",
        "urls": ["https://cohere.com/blog"],
        "topics": ["nlp-infrastructure", "text-generation", "embedding-services", "enterprise-ai"],
        "category": "AI/ML"
    },

    # ==================== ADDITIONAL TECH GIANTS ====================
    {
        "name": "Salesforce",
        "urls": ["https://engineering.salesforce.com/"],
        "topics": ["crm-architecture", "multi-tenant-cloud", "api-ecosystem", "enterprise-scale"],
        "category": "Enterprise"
    },
    {
        "name": "Oracle",
        "urls": ["https://blogs.oracle.com/"],
        "topics": ["database-systems", "enterprise-cloud", "distributed-transactions", "autonomous-db"],
        "category": "Enterprise"
    },
    {
        "name": "IBM",
        "urls": ["https://www.ibm.com/blogs/"],
        "topics": ["quantum-computing", "watson-ai", "enterprise-systems", "hybrid-cloud"],
        "category": "Enterprise"
    },
    {
        "name": "Cisco",
        "urls": ["https://blogs.cisco.com/"],
        "topics": ["networking-infrastructure", "sdn-architecture", "security-systems", "iot-platforms"],
        "category": "Enterprise"
    },
    {
        "name": "VMware",
        "urls": ["https://blogs.vmware.com/"],
        "topics": ["virtualization", "cloud-infrastructure", "container-orchestration", "software-defined-datacenter"],
        "category": "Enterprise"
    },
    {
        "name": "SAP",
        "urls": ["https://blogs.sap.com/"],
        "topics": ["erp-systems", "enterprise-cloud", "business-intelligence", "supply-chain-tech"],
        "category": "Enterprise"
    },
    {
        "name": "Adobe",
        "urls": ["https://medium.com/adobetech"],
        "topics": ["creative-cloud", "document-processing", "ai-powered-tools", "media-processing"],
        "category": "Enterprise"
    },
    {
        "name": "Intuit",
        "urls": ["https://medium.com/intuit-engineering"],
        "topics": ["financial-software", "tax-processing", "small-business-platform", "ml-fraud-detection"],
        "category": "Enterprise"
    },
    {
        "name": "ServiceNow",
        "urls": ["https://developer.servicenow.com/blog/"],
        "topics": ["workflow-automation", "enterprise-platform", "it-service-management", "low-code"],
        "category": "Enterprise"
    },
    {
        "name": "Splunk",
        "urls": ["https://www.splunk.com/blog"],
        "topics": ["log-analytics", "security-monitoring", "data-ingestion", "real-time-processing"],
        "category": "Enterprise"
    },
    {
        "name": "Palantir",
        "urls": ["https://blog.palantir.com/"],
        "topics": ["data-integration", "analytics-platform", "graph-database", "enterprise-search"],
        "category": "Enterprise"
    },
    {
        "name": "Snowflake",
        "urls": ["https://www.snowflake.com/blog/"],
        "topics": ["data-warehouse", "cloud-architecture", "query-optimization", "data-sharing"],
        "category": "Enterprise"
    },
    {
        "name": "Databricks",
        "urls": ["https://www.databricks.com/blog"],
        "topics": ["lakehouse", "spark-optimization", "ml-platform", "unified-analytics"],
        "category": "Enterprise"
    },
    {
        "name": "Atlassian",
        "urls": ["https://www.atlassian.com/engineering"],
        "topics": ["collaboration-tools", "jira-architecture", "confluence-scale", "developer-workflow"],
        "category": "Enterprise"
    },
    {
        "name": "Zoom",
        "urls": ["https://blog.zoom.us/"],
        "topics": ["video-conferencing", "real-time-communication", "media-processing", "global-infrastructure"],
        "category": "Enterprise"
    },
    {
        "name": "Dropbox",
        "urls": ["https://dropbox.tech/"],
        "topics": ["file-sync", "distributed-storage", "block-level-sync", "sharing-platform"],
        "category": "Enterprise"
    },
    {
        "name": "Box",
        "urls": ["https://blog.box.com/blog/engineering"],
        "topics": ["content-management", "enterprise-cloud", "security-compliance", "collaboration"],
        "category": "Enterprise"
    },
    {
        "name": "Notion",
        "urls": ["https://www.notion.so/blog"],
        "topics": ["collaborative-editing", "real-time-sync", "block-editor", "database-engine"],
        "category": "Enterprise"
    },
    {
        "name": "Figma",
        "urls": ["https://www.figma.com/blog/"],
        "topics": ["collaborative-design", "webgl-rendering", "real-time-cursors", "vector-engine"],
        "category": "Enterprise"
    },
    {
        "name": "Canva",
        "urls": ["https://www.canva.dev/blog/engineering/"],
        "topics": ["design-platform", "image-processing", "collaboration-tools", "template-engine", "generative-ai-design", "ai-content-creation", "multimodal-generation"],
        "category": "Enterprise"
    },

    # ==================== ADDITIONAL AI/ML COMPANIES ====================
    {
        "name": "Mistral AI",
        "urls": ["https://mistral.ai/news/"],
        "topics": ["llm-architecture", "open-source-ai", "generative-ai-models", "agentic-ai-frameworks", "efficient-inference", "multilingual-models", "mixture-of-experts", "ai-deployment-optimization"],
        "category": "AI/ML"
    },
    {
        "name": "AI21 Labs",
        "urls": ["https://www.ai21.com/blog"],
        "topics": ["llm-development", "generative-ai-writing", "text-generation", "ai-reasoning-systems", "agentic-ai-planning", "context-window-optimization", "enterprise-ai-solutions"],
        "category": "AI/ML"
    },
    {
        "name": "Inflection AI",
        "urls": ["https://inflection.ai/"],
        "topics": ["conversational-ai", "llm-infrastructure", "generative-ai-assistants", "agentic-ai-memory", "personalized-ai-systems", "multi-turn-dialogue", "ai-safety-alignment"],
        "category": "AI/ML"
    },
    {
        "name": "Adept AI",
        "urls": ["https://www.adept.ai/blog"],
        "topics": ["agentic-ai-actions", "ai-automation-systems", "llm-tool-use", "generative-workflows", "computer-use-models", "action-oriented-ai", "human-ai-collaboration"],
        "category": "AI/ML"
    },
    {
        "name": "Character.AI",
        "urls": ["https://blog.character.ai/"],
        "topics": ["conversational-agents", "llm-personalization", "generative-ai-characters", "agentic-ai-personas", "multi-agent-systems", "ai-memory-systems", "role-playing-architecture"],
        "category": "AI/ML"
    },
    {
        "name": "Perplexity AI",
        "urls": ["https://www.perplexity.ai/hub"],
        "topics": ["retrieval-augmented-generation", "generative-ai-search", "agentic-ai-research", "real-time-web-search", "ai-answer-systems", "citation-generation", "conversational-search"],
        "category": "AI/ML"
    },
    {
        "name": "Cursor",
        "urls": ["https://www.cursor.com/blog"],
        "topics": ["agentic-ai-coding", "llm-code-generation", "generative-ai-development", "ai-pair-programming", "code-completion-systems", "multi-file-editing", "context-aware-ai"],
        "category": "AI/ML"
    },
    {
        "name": "Replit",
        "urls": ["https://blog.replit.com/"],
        "topics": ["agentic-ai-development", "llm-code-generation", "generative-programming", "ai-coding-assistant", "interactive-development", "code-interpretation", "multi-language-support"],
        "category": "AI/ML"
    },
    {
        "name": "DevCycle",
        "urls": ["https://www.devcycle.com/blog"],
        "topics": ["feature-flag-systems", "ai-powered-testing", "generative-ai-config", "agentic-deployment-pipelines", "ml-rollout-strategies", "canary-deployments"],
        "category": "AI/ML"
    },
    {
        "name": "Pinecone",
        "urls": ["https://www.pinecone.io/blog/"],
        "topics": ["vector-database", "semantic-search", "embedding-storage", "retrieval-augmented-generation", "similarity-search-systems", "agentic-ai-memory", "high-dimensional-indexing"],
        "category": "AI/ML"
    },
    {
        "name": "Milvus",
        "urls": ["https://milvus.io/blog"],
        "topics": ["vector-search-engine", "similarity-matching", "embedding-management", "generative-ai-retrieval", "distributed-vector-db", "agentic-ai-knowledge", "hybrid-search-systems"],
        "category": "AI/ML"
    },
    {
        "name": "Chroma",
        "urls": ["https://www.trychroma.com/blog"],
        "topics": ["vector-database", "embedding-storage", "retrieval-systems", "agentic-ai-memory", "semantic-search", "generative-ai-context", "lightweight-vector-search"],
        "category": "AI/ML"
    },
    {
        "name": "Anyscale",
        "urls": ["https://www.anyscale.com/blog"],
        "topics": ["distributed-computing", "ray-framework", "ml-training-scale", "agentic-ai-orchestration", "generative-model-serving", "multi-agent-systems", "gpu-cluster-management"],
        "category": "AI/ML"
    },
    {
        "name": "Modal",
        "urls": ["https://modal.com/blog"],
        "topics": ["serverless-gpu", "ml-deployment", "ai-inference-serving", "generative-ai-infrastructure", "agentic-compute", "model-serving-optimization", "cloud-native-ai"],
        "category": "AI/ML"
    },
    {
        "name": "Replicate",
        "urls": ["https://replicate.com/blog"],
        "topics": ["ml-model-hosting", "generative-ai-api", "model-deployment", "ai-inference-optimization", "agentic-ai-services", "open-source-models", "serverless-ml"],
        "category": "AI/ML"
    },
    {
        "name": "Baseten",
        "urls": ["https://www.baseten.co/blog"],
        "topics": ["ml-inference", "model-serving", "generative-ai-deployment", "ai-pipeline-optimization", "agentic-workflows", "gpu-utilization", "model-versioning"],
        "category": "AI/ML"
    },
]


def get_random_companies(count=3):
    """Get random companies for exploration."""
    import random
    return random.sample(TECH_COMPANIES, min(count, len(TECH_COMPANIES)))


def get_companies_by_category(category):
    """Get all companies in a category."""
    return [c for c in TECH_COMPANIES if c['category'] == category]


def get_all_categories():
    """Get all available categories."""
    return list(set(c['category'] for c in TECH_COMPANIES))


if __name__ == "__main__":
    print(f"Total companies: {len(TECH_COMPANIES)}")
    print(f"Categories: {get_all_categories()}")
    
    # Show sample
    print("\nSample companies:")
    for company in TECH_COMPANIES[:5]:
        print(f"  - {company['name']} ({company['category']}): {', '.join(company['topics'][:3])}")
