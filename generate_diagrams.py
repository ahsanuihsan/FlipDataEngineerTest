#!/usr/bin/env python3
"""
Generate Data Architecture Diagram
"""
from graphviz import Digraph

def create_architecture_diagram():
    """Create comprehensive data architecture diagram"""
    
    # Create main graph
    dot = Digraph(comment='Pokemon Data Architecture', format='png')
    dot.attr(rankdir='TB', size='12,16')
    dot.attr('node', shape='box', style='rounded,filled', fontname='Arial')
    
    # Define color scheme
    color_source = '#E3F2FD'
    color_ingestion = '#FFF9C4'
    color_staging = '#FFCCBC'
    color_ods = '#C8E6C9'
    color_dwh = '#E1BEE7'
    color_analytics = '#FFECB3'
    
    # Data Sources
    with dot.subgraph(name='cluster_sources') as c:
        c.attr(label='Data Sources', style='filled', color='lightgrey')
        c.node('api', 'PokeAPI\n(External REST API)', fillcolor=color_source)
        c.node('user', 'User Input\n(FastAPI POST)', fillcolor=color_source)
    
    # Ingestion Layer
    with dot.subgraph(name='cluster_ingestion') as c:
        c.attr(label='Ingestion Layer', style='filled', color='lightgrey')
        c.node('fastapi', 'FastAPI Application\n• Input Validation\n• API Calls\n• Orchestration', 
               fillcolor=color_ingestion, shape='box3d')
    
    # Staging Layer
    with dot.subgraph(name='cluster_staging') as c:
        c.attr(label='STAGING LAYER', style='filled', color='lightgrey')
        c.node('staging_raw', 'stg_pokemon_raw\n• Raw JSON\n• Timestamps\n• Metadata', 
               fillcolor=color_staging)
        c.node('staging_logs', 'stg_api_logs\n• API Logs\n• Response Times\n• Errors', 
               fillcolor=color_staging)
    
    # ODS Layer
    with dot.subgraph(name='cluster_ods') as c:
        c.attr(label='OPERATIONAL DATA STORE (ODS)', style='filled', color='lightgrey')
        c.node('ods_abilities', 'pokemon_abilities\n[Current Implementation]\n• Normalized Data\n• Real-time Access', 
               fillcolor=color_ods, penwidth='3')
        c.node('ods_pokemon', 'pokemon_master\n• Pokemon Details\n• Attributes', 
               fillcolor=color_ods)
        c.node('ods_ability', 'ability_master\n• Ability Details\n• Metadata', 
               fillcolor=color_ods)
        c.node('ods_language', 'language_master\n• Language Details', 
               fillcolor=color_ods)
    
    # Data Warehouse Layer
    with dot.subgraph(name='cluster_dwh') as c:
        c.attr(label='DATA WAREHOUSE LAYER', style='filled', color='lightgrey')
        
        # Fact Tables
        c.node('fact_requests', 'fact_ability_requests\n• Request Metrics\n• Response Times\n• Success Rates', 
               fillcolor=color_dwh, shape='cylinder')
        c.node('fact_usage', 'fact_pokemon_usage\n• Usage Analytics\n• Aggregated Data', 
               fillcolor=color_dwh, shape='cylinder')
        
        # Dimension Tables
        c.node('dim_pokemon', 'dim_pokemon\n[SCD Type 2]\n• Historical Changes', 
               fillcolor=color_dwh)
        c.node('dim_ability', 'dim_ability\n[SCD Type 2]\n• Historical Changes', 
               fillcolor=color_dwh)
        c.node('dim_user', 'dim_user\n[SCD Type 1]', fillcolor=color_dwh)
        c.node('dim_date', 'dim_date\n[Pre-populated]', fillcolor=color_dwh)
    
    # Analytics Layer
    with dot.subgraph(name='cluster_analytics') as c:
        c.attr(label='Analytics & Reporting', style='filled', color='lightgrey')
        c.node('bi', 'BI Tools\n• Tableau\n• Power BI\n• Metabase', fillcolor=color_analytics)
        c.node('reports', 'Reports & Dashboards\n• Usage Analytics\n• Performance Metrics\n• Trends', 
               fillcolor=color_analytics)
    
    # Define data flow edges
    # Sources to Ingestion
    dot.edge('api', 'fastapi', label='JSON Response')
    dot.edge('user', 'fastapi', label='POST Request')
    
    # Ingestion to Staging
    dot.edge('fastapi', 'staging_raw', label='Raw Data\n(Real-time)')
    dot.edge('fastapi', 'staging_logs', label='API Logs\n(Real-time)')
    
    # Staging to ODS
    dot.edge('staging_raw', 'ods_abilities', label='ETL\n(Every 5 min)')
    dot.edge('staging_raw', 'ods_pokemon', label='Parse & Normalize')
    dot.edge('staging_raw', 'ods_ability', label='Parse & Normalize')
    dot.edge('staging_raw', 'ods_language', label='Parse & Normalize')
    
    # ODS to DWH Facts
    dot.edge('ods_abilities', 'fact_requests', label='Daily Batch\n(2 AM)')
    dot.edge('ods_abilities', 'fact_usage', label='Aggregate')
    
    # ODS to DWH Dimensions
    dot.edge('ods_pokemon', 'dim_pokemon', label='SCD Type 2')
    dot.edge('ods_ability', 'dim_ability', label='SCD Type 2')
    dot.edge('ods_language', 'dim_date', label='Reference')
    
    # DWH to Analytics
    dot.edge('fact_requests', 'bi', label='Query')
    dot.edge('fact_usage', 'bi', label='Query')
    dot.edge('dim_pokemon', 'bi', label='Join')
    dot.edge('dim_ability', 'bi', label='Join')
    dot.edge('dim_user', 'bi', label='Join')
    dot.edge('dim_date', 'bi', label='Join')
    
    dot.edge('bi', 'reports', label='Visualize')
    
    return dot

def create_simplified_diagram():
    """Create simplified architecture diagram"""
    
    dot = Digraph(comment='Simplified Data Flow', format='png')
    dot.attr(rankdir='LR', size='14,8')
    dot.attr('node', shape='box', style='rounded,filled', fontname='Arial', fontsize='12')
    
    # Define nodes
    dot.node('1', 'API Request\n(User Input)', fillcolor='#E3F2FD')
    dot.node('2', 'FastAPI\nApplication', fillcolor='#FFF9C4', shape='box3d')
    dot.node('3', 'PokeAPI\nFetch Data', fillcolor='#FFE082')
    dot.node('4', 'STAGING\n(Raw JSON)', fillcolor='#FFCCBC')
    dot.node('5', 'ODS\n(Normalized)', fillcolor='#C8E6C9')
    dot.node('6', 'DWH\n(Star Schema)', fillcolor='#E1BEE7')
    dot.node('7', 'BI & Reports\n(Analytics)', fillcolor='#FFECB3')
    
    # Define edges with labels
    dot.edge('1', '2', label='POST JSON')
    dot.edge('2', '3', label='HTTP GET')
    dot.edge('3', '2', label='JSON Response')
    dot.edge('2', '4', label='Store Raw\n(Real-time)')
    dot.edge('4', '5', label='ETL\n(5 min)')
    dot.edge('5', '6', label='Daily Batch\n(2 AM)')
    dot.edge('6', '7', label='SQL Query')
    dot.edge('2', '1', label='Return Result')
    
    return dot

if __name__ == "__main__":
    print("Generating data architecture diagrams...")
    
    # Generate comprehensive diagram
    comprehensive = create_architecture_diagram()
    comprehensive.render('data-architecture-comprehensive', cleanup=True)
    print("✓ Generated: data-architecture-comprehensive.png")
    
    # Generate simplified diagram
    simplified = create_simplified_diagram()
    simplified.render('data-architecture-simplified', cleanup=True)
    print("✓ Generated: data-architecture-simplified.png")
    
    print("\nDiagrams generated successfully!")
    print("\nFiles created:")
    print("  1. data-architecture-comprehensive.png - Detailed architecture")
    print("  2. data-architecture-simplified.png - Simplified data flow")
