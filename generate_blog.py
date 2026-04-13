"""Quick blog generator - generates one post immediately."""
import asyncio
from pathlib import Path
from datetime import datetime
from src.config import Config
from src.models.data_models import ContentItem, BlogPost
from src.agents.publisher import PublisherAgent


async def generate_blog():
    """Generate a blog post about Big Tech architecture."""
    
    print("=" * 70)
    print("🚀 Quick Blog Generator - Big Tech Architecture")
    print("=" * 70)
    
    # Create sample content about Big Tech
    content_item = ContentItem(
        title="Google's Distributed System Architecture: 20+ Years of Scale",
        author="Google Engineering Blog",
        publication_date=datetime(2024, 1, 20),
        url="https://blog.google/technology/infrastructure",
        text_content="""Google handles billions of searches daily through one of the world's most sophisticated distributed systems. Their architecture spans multiple continents, processes exabytes of data, and serves results in milliseconds.

Key components include:
- Borg: Container orchestration system (predates Kubernetes)
- Spanner: Globally distributed database with strong consistency
- Colossus: Distributed file system handling exabytes
- Dapper: Distributed tracing system for debugging
- SRE: Site Reliability Engineering practices

Google's infrastructure demonstrates that with proper design, systems can scale to serve billions of users while maintaining reliability and performance.""",
        code_blocks=[],
        images=[],
        metadata={"topic": "google-architecture"}
    )
    
    print("\n📝 Generating blog post...")
    
    # Create blog post directly (skip LLM for speed)
    blog_post = BlogPost(
        title="Inside Google's Planet-Scale Infrastructure: Architectural Lessons",
        content="""# Inside Google's Planet-Scale Infrastructure: Architectural Lessons

## Introduction

When you search on Google, you're interacting with one of the most sophisticated distributed systems ever built. Google processes over 8.5 billion searches daily, serving results in under 200 milliseconds from data centers spanning every continent.

How do they do it? Let's explore the architectural decisions that make this possible.

## Borg: The Original Container Orchestrator

Long before Kubernetes became the industry standard, Google ran **Borg**—an internal container orchestration system that managed millions of containers across thousands of machines.

**Key Design Principles:**
- Jobs are scheduled based on resource requirements, not specific machines
- Automatic failover when machines fail
- Resource isolation through containers
- Priority-based preemption for critical workloads

**Lesson for System Design:** Build automation into every layer. Google doesn't manually schedule workloads—they let the system optimize itself.

## Spanner: Globally Consistent Database

Google needed a database that could:
- Scale globally across multiple data centers
- Maintain strong consistency (not eventual)
- Survive regional failures without data loss
- Handle billions of transactions per second

Enter **Spanner**—a globally distributed database that uses atomic clocks and GPS receivers to synchronize time across data centers worldwide.

**How It Works:**
1. TrueTime API provides globally synchronized timestamps
2. Transactions commit in timestamp order
3. Read operations see consistent snapshots
4. Automatic failover across regions

**Lesson:** When consistency matters globally, innovate at the hardware level.

## Colossus: Distributed File System at Exabyte Scale

Google's file system handles exabytes of data across millions of machines. The current version, **Colossus**, improves on the original GFS with:

- Better fault tolerance
- Improved performance for parallel reads
- Automatic data replication
- Cross-datacenter redundancy

**Lesson:** Design storage systems for the failure case, not the success case.

## Dapper: Distributed Tracing

With thousands of microservices handling each request, how do you debug problems? Google built **Dapper**, a distributed tracing system that:

- Tracks requests across service boundaries
- Identifies performance bottlenecks
- Provides visibility into system behavior
- Enables data-driven optimization

Dapper inspired open-source tools like **Jaeger** and **Zipkin**, now industry standards.

**Lesson:** Observability isn't optional at scale—it's essential.

## SRE: Site Reliability Engineering

Google pioneered the SRE role—software engineers who operate production systems. Key practices:

### Error Budgets
- Define acceptable error rate (e.g., 99.9% availability)
- Use remaining budget for feature launches
- Stop launches when budget is exhausted
- Focus on reliability over velocity

### Toil Elimination
- Automate repetitive operational work
- SREs spend 50% on ops, 50% on development
- Every manual task becomes an automation target

**Lesson:** Treat operations as a software problem, not a manual process.

## Infrastructure Design Patterns

From Google's architecture, we can extract universal patterns:

### 1. Design for Failure
- Assume everything fails: networks, disks, machines, data centers
- Build redundancy at every layer
- Test failure regularly (Chaos Engineering)

### 2. Automate Everything
- No manual interventions in production
- Self-healing systems detect and recover from failures
- Automated scaling based on demand

### 3. Global from Day One
- Design for multiple regions even if you start with one
- Use consistent abstractions across regions
- Plan for data sovereignty requirements

### 4. Observability First
- Instrument every component
- Centralize logging and metrics
- Build dashboards before you need them

### 5. Incremental Rollouts
- Deploy to small percentage first
- Monitor metrics closely
- Roll back automatically if issues detected

## Practical Takeaways for Your Systems

You don't need Google's budget to apply these principles:

1. **Start with observability**: Add logging and metrics before production
2. **Automate deployments**: CI/CD pipeline from day one
3. **Design for failure**: What happens when your database goes down?
4. **Use proven patterns**: API gateway, circuit breaker, service mesh
5. **Monitor error budgets**: Define SLOs and track them
6. **Practice incident response**: Run game days and chaos tests

## Conclusion

Google's infrastructure represents decades of learning about distributed systems. While most companies won't build Spanner or Colossus, the underlying principles apply at any scale:

- **Automate** operational tasks
- **Design** for failure scenarios
- **Measure** everything continuously
- **Learn** from incidents systematically
- **Share** knowledge through open source

The companies that succeed at scale aren't those with the biggest budgets—they're those that build systems expecting failure, embracing automation, and learning from every incident.

Google's open-source contributions (Kubernetes, TensorFlow, Istio) prove that sharing knowledge benefits the entire industry. What patterns will your team contribute next?
""",
        tags=["google", "distributed-systems", "system-design", "architecture", "scalability", "devops"],
        word_count=850,
        source_url="https://blog.google/technology/infrastructure",
        generated_at=datetime.utcnow()
    )
    
    print(f"✅ Blog post generated: {blog_post.title}")
    print(f"   Word count: {blog_post.word_count}")
    print(f"   Tags: {', '.join(blog_post.tags)}")
    
    print("\n💾 Saving as local draft...")
    
    publisher = PublisherAgent()
    result = await publisher.publish(blog_post)
    
    if result.success:
        print(f"\n{'=' * 70}")
        print("✅ SUCCESS! Blog post saved!")
        print(f"{'=' * 70}")
        print(f"\n📁 Location: {result.post_url}")
        
        # Display the file
        if result.post_url and Path(result.post_url).exists():
            print(f"\n{'=' * 70}")
            print("📖 FULL CONTENT:")
            print(f"{'=' * 70}")
            with open(result.post_url, 'r', encoding='utf-8') as f:
                print(f.read())
    else:
        print(f"\n❌ Failed to save: {result.error}")


if __name__ == "__main__":
    asyncio.run(generate_blog())
