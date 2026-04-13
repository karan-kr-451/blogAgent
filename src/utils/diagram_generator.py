"""
Diagram Generator - Creates architecture diagrams, workflow charts, and visual examples.

Generates Mermaid.js diagrams for blog posts, similar to the ones in design.md
"""
from typing import Literal


class DiagramGenerator:
    """Generates Mermaid diagrams for system design blog posts."""
    
    @staticmethod
    def generate_system_architecture(
        system_name: str,
        components: list[str],
        databases: list[str] | None = None,
        external_services: list[str] | None = None
    ) -> str:
        """
        Generate a system architecture diagram.
        
        Args:
            system_name: Name of the system
            components: List of system components
            databases: List of databases
            external_services: List of external services
        
        Returns:
            Mermaid diagram code
        """
        lines = [f"```mermaid", f"graph TB", f"    subgraph {system_name}", ""]
        
        # Add components
        for i, comp in enumerate(components):
            label = f"C{i+1}[{comp}]"
            lines.append(f"    {label}")
        
        lines.append("    end")
        lines.append("")
        
        # Add databases
        if databases:
            lines.append("    subgraph Data Layer")
            for i, db in enumerate(databases):
                label = f"D{i+1}[({db})]"
                lines.append(f"    {label}")
            lines.append("    end")
            lines.append("")
            
            # Connect components to databases
            lines.append(f"    C1 --> D1")
            if len(databases) > 1:
                lines.append(f"    C2 --> D2")
        
        # Add external services
        if external_services:
            lines.append("")
            lines.append("    subgraph External Services")
            for i, svc in enumerate(external_services):
                label = f"E{i+1}[{svc}]"
                lines.append(f"    {label}")
            lines.append("    end")
            lines.append("")
            lines.append(f"    C1 --> E1")
        
        # Connect components
        if len(components) > 1:
            lines.append("")
            lines.append("    %% Component interactions")
            for i in range(len(components) - 1):
                lines.append(f"    C{i+1} --> C{i+2}")
        
        lines.append("```")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_sequence_diagram(
        title: str,
        actors: list[str],
        steps: list[tuple[str, str, str]]
    ) -> str:
        """
        Generate a sequence diagram.
        
        Args:
            title: Diagram title
            actors: List of actors/participants
            steps: List of (from, to, message) tuples
        
        Returns:
            Mermaid sequence diagram code
        """
        lines = [f"```mermaid", f"sequenceDiagram", f"    title {title}", ""]
        
        # Add participants
        for i, actor in enumerate(actors):
            lines.append(f"    participant {actor}")
        
        lines.append("")
        
        # Add steps
        for from_actor, to_actor, message in steps:
            lines.append(f"    {from_actor}->>{to_actor}: {message}")
        
        lines.append("```")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_workflow_chart(
        title: str,
        steps: list[tuple[str, str]],  # (step_name, next_step)
        decision_points: list[tuple[str, str, str]] | None = None  # (decision, yes_path, no_path)
    ) -> str:
        """
        Generate a workflow flowchart.
        
        Args:
            title: Chart title
            steps: List of (step_name, next_step) tuples
            decision_points: List of (decision, yes_path, no_path) tuples
        
        Returns:
            Mermaid flowchart code
        """
        lines = [f"```mermaid", f"graph TD", f"    title {title}", ""]
        
        # Add steps
        for i, (step, next_step) in enumerate(steps):
            label = f"S{i+1}[{step}]"
            lines.append(f"    {label}")
        
        lines.append("")
        
        # Add connections
        for i, (step, next_step) in enumerate(steps):
            if next_step:
                # Find index of next step
                for j, (s, _) in enumerate(steps):
                    if s == next_step:
                        lines.append(f"    S{i+1} --> S{j+1}")
                        break
        
        # Add decision points
        if decision_points:
            lines.append("")
            for i, (decision, yes_path, no_path) in enumerate(decision_points):
                label = f"D{i+1}{{{decision}}}"
                lines.append(f"    {label}")
                lines.append(f"    D{i+1} -->|Yes| {yes_path}")
                lines.append(f"    D{i+1} -->|No| {no_path}")
        
        lines.append("```")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_data_flow_diagram(
        title: str,
        components: dict[str, list[str]]  # component_name -> [inputs/outputs]
    ) -> str:
        """
        Generate a data flow diagram.
        
        Args:
            title: Diagram title
            components: Dict of component_name -> [inputs/outputs]
        
        Returns:
            Mermaid data flow diagram code
        """
        lines = [f"```mermaid", f"graph LR", f"    title {title}", ""]
        
        # Add components
        for i, (name, flows) in enumerate(components.items()):
            label = f"F{i+1}[{name}]"
            lines.append(f"    {label}")
        
        lines.append("")
        
        # Add flows
        component_list = list(components.keys())
        for i in range(len(component_list) - 1):
            lines.append(f"    F{i+1} --> F{i+2}")
        
        lines.append("```")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_deployment_diagram(
        environment: str,
        services: list[str],
        infrastructure: list[str]
    ) -> str:
        """
        Generate a deployment diagram.
        
        Args:
            environment: Environment name (Production, Staging, etc.)
            services: List of services
            infrastructure: List of infrastructure components
        
        Returns:
            Mermaid deployment diagram code
        """
        lines = [f"```mermaid", f"graph TB", f"    subgraph {environment}", ""]
        
        # Add services
        for i, svc in enumerate(services):
            lines.append(f"    S{i+1}[{svc}]")
        
        lines.append("    end")
        lines.append("")
        
        # Add infrastructure
        lines.append("    subgraph Infrastructure")
        for i, infra in enumerate(infrastructure):
            lines.append(f"    I{i+1}[{infra}]")
        lines.append("    end")
        lines.append("")
        
        # Connect services to infrastructure
        lines.append("    S1 --> I1")
        if len(services) > 1:
            lines.append("    S2 --> I2")
        
        lines.append("```")
        
        return "\n".join(lines)


# Pre-built diagram templates for common architectures
DIAGRAM_TEMPLATES = {
    "microservices": {
        "architecture": {
            "components": ["API Gateway", "Auth Service", "User Service", "Order Service", "Payment Service"],
            "databases": ["User DB", "Order DB", "Payment DB"],
            "external_services": ["Message Queue", "Cache Layer", "Monitoring"]
        }
    },
    "data_pipeline": {
        "workflow": {
            "title": "Data Processing Pipeline",
            "steps": [
                ("Data Ingestion", "Validation"),
                ("Validation", "Transformation"),
                ("Transformation", "Enrichment"),
                ("Enrichment", "Storage"),
                ("Storage", "Analytics")
            ]
        }
    },
    "web_application": {
        "architecture": {
            "components": ["Load Balancer", "Web Server", "App Server", "Background Worker"],
            "databases": ["Primary DB", "Replica DB", "Cache"],
            "external_services": ["CDN", "Object Storage"]
        }
    }
}


if __name__ == "__main__":
    # Test diagram generation
    generator = DiagramGenerator()
    
    # Test system architecture
    arch_diagram = generator.generate_system_architecture(
        "Microservices Architecture",
        ["API Gateway", "User Service", "Order Service", "Payment Service"],
        ["PostgreSQL", "Redis Cache"],
        ["Message Queue", "External API"]
    )
    
    print("System Architecture Diagram:")
    print(arch_diagram)
    print()
    
    # Test sequence diagram
    seq_diagram = generator.generate_sequence_diagram(
        "User Authentication Flow",
        ["Client", "API Gateway", "Auth Service", "User DB"],
        [
            ("Client", "API Gateway", "Login Request"),
            ("API Gateway", "Auth Service", "Validate Credentials"),
            ("Auth Service", "User DB", "Query User"),
            ("User DB", "Auth Service", "User Data"),
            ("Auth Service", "API Gateway", "JWT Token"),
            ("API Gateway", "Client", "Authentication Response")
        ]
    )
    
    print("Sequence Diagram:")
    print(seq_diagram)
