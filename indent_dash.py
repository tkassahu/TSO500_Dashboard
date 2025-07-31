from shiny import App, Inputs, Outputs, Session, render, ui, reactive
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from neo4j import GraphDatabase
import os
from datetime import datetime
import matplotlib.patches as patches
from matplotlib.patches import Rectangle
import warnings
import io
import base64
warnings.filterwarnings('ignore')

# Configure matplotlib for better rendering
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
matplotlib.rcParams['figure.autolayout'] = False
matplotlib.rcParams['figure.constrained_layout.use'] = False
matplotlib.rcParams['figure.dpi'] = 100
matplotlib.rcParams['savefig.dpi'] = 100
matplotlib.rcParams['figure.max_open_warning'] = 50

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION & DATABASE CONNECTION
# ═══════════════════════════════════════════════════════════════

# Neo4j/Memgraph connection
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# ═══════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════

def load_data():
    """Load all CSV files"""
    try:
        demographics_df = pd.read_csv('clean_demographics.csv')
        variants_df = pd.read_csv('variants_with_50_demo_mrn_200pts.csv')
        
        # Try different filenames for variants
        if not os.path.exists('variants_with_50_demo_mrn_200pts.csv'):
            if os.path.exists('TSO500_Synthetic_Final.csv'):
                variants_df = pd.read_csv('TSO500_Synthetic_Final.csv')
            else:
                variants_df = pd.read_csv('variants_with_50_demo_mrn.csv')
        
        protocols_df = pd.read_csv('protocols.csv')
        subjects_df = pd.read_csv('clinical_trial_subjects.csv')
        interventions_df = pd.read_csv('interventions.csv')
        adverse_events_df = pd.read_csv('adverse_events.csv')
        
        # Merge variants with demographics
        merged_df = pd.merge(variants_df, demographics_df, on='mrn', how='left')
        
        return {
            'demographics': demographics_df,
            'variants': variants_df,
            'merged': merged_df,
            'protocols': protocols_df,
            'subjects': subjects_df,
            'interventions': interventions_df,
            'adverse_events': adverse_events_df
        }
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

# Load data
data = load_data()

# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def summary_card(title, value, icon="📊"):
    """Create a summary card with title and value"""
    return ui.div(
        ui.div(
            ui.span(icon, style="font-size: 1.5rem; margin-right: 8px;"),
            ui.h4(title, style="margin: 0; font-weight: 500;"),
            style="display: flex; align-items: center; margin-bottom: 8px;"
        ),
        ui.h2(str(value), style="margin: 0; color: #2c3e50;"),
        class_="summary-card",
        style="""
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #3498db;
        """
    )

def plot_card(title, plot_func):
    """Create a card containing a plot"""
    return ui.div(
        ui.h4(title, style="margin: 0 0 15px 0; color: #2c3e50;"),
        plot_func,
        class_="plot-card",
        style="""
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            height: 100%;
            overflow: visible;
        """
    )

def run_cypher_query(query, parameters=None):
    """Execute a Cypher query and return results"""
    with driver.session() as session:
        result = session.run(query, parameters or {})
        return [record.data() for record in result]

# ═══════════════════════════════════════════════════════════════
# UI DEFINITION
# ═══════════════════════════════════════════════════════════════

app_ui = ui.page_fluid(
    # Custom CSS
    ui.tags.head(
        ui.tags.style("""
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background-color: #f5f7fa;
            }
            .nav-link { 
                font-weight: 500; 
                padding: 12px 24px !important;
            }
            .nav-link.active {
                background-color: #3498db !important;
                color: white !important;
            }
            .filter-section {
                background: white;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .filter-section h4 {
                margin-top: 0;
                margin-bottom: 15px;
                color: #2c3e50;
                border-bottom: 2px solid #ecf0f1;
                padding-bottom: 10px;
            }
            .plot-card {
                overflow: visible !important;
            }
            .shiny-plot-output {
                overflow: visible !important;
            }
            .col-sm-4, .col-sm-6, .col-sm-12 {
                min-height: 400px;
            }
        """)
    ),
    
    # Header
    ui.div(
        ui.h1("Clinical Data and Molecular Profiling Dashboard", 
              style="margin: 0; color: white; font-weight: 300;"),
        style="""
            background: linear-gradient(135deg, #3498db, #2c3e50);
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        """
    ),
    
    # Main content with tabs
    ui.div(
        ui.navset_tab(
            # ═══════════════════════════════════════════════════════════════
            # DEMOGRAPHICS TAB
            # ═══════════════════════════════════════════════════════════════
            ui.nav_panel(
                "Demographics",
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.div(
                            ui.h4("Demographics Filters"),
                            ui.input_checkbox_group(
                                "demo_sex_filter",
                                "Sex:",
                                choices={"male": "Male", "female": "Female"},
                                selected=["male", "female"]
                            ),
                            ui.input_slider(
                                "demo_age_filter",
                                "Age Range:",
                                min=18,
                                max=85,
                                value=[18, 85],
                                step=1
                            ),
                            class_="filter-section"
                        ),
                        width=300
                    ),
                    ui.row(
                        ui.column(6, 
                            ui.div(
                                ui.h4("Age Distribution", style="margin-bottom: 15px;"),
                                ui.output_plot("age_distribution", height="450px"),
                                style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"
                            )
                        ),
                        ui.column(6, 
                            ui.div(
                                ui.h4("Sex Distribution", style="margin-bottom: 15px;"),
                                ui.output_plot("sex_distribution", height="450px"),
                                style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"
                            )
                        )
                    ),
                    ui.row(
                        ui.column(12, 
                            ui.h4("Patient Summary", style="margin-top: 20px;"),
                            ui.output_ui("demographics_summary")
                        )
                    )
                )
            ),
            
            # ═══════════════════════════════════════════════════════════════
            # GENOMICS TAB
            # ═══════════════════════════════════════════════════════════════
            ui.nav_panel(
                "Genomics",
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.div(
                            ui.h4("Genomics Filters"),
                            ui.input_selectize(
                                "gene_filter",
                                "Filter by Gene:",
                                choices=["All"] + sorted(data['variants']['gene'].unique().tolist()),
                                selected="All",
                                multiple=False
                            ),
                            ui.input_checkbox_group(
                                "assessment_filter",
                                "Clinical Assessment:",
                                choices={
                                    "Pathogenic": "Pathogenic",
                                    "Likely Pathogenic": "Likely Pathogenic",
                                    "VUS": "VUS",
                                    "Likely Benign": "Likely Benign",
                                    "Benign": "Benign"
                                },
                                selected=["Pathogenic", "Likely Pathogenic", "VUS", "Likely Benign", "Benign"]
                            ),
                            class_="filter-section"
                        ),
                        width=300
                    ),
                    # Summary cards
                    ui.row(
                        ui.column(3, ui.output_ui("total_variants_card")),
                        ui.column(3, ui.output_ui("unique_genes_card")),
                        ui.column(3, ui.output_ui("pathogenic_count_card")),
                        ui.column(3, ui.output_ui("actionable_count_card"))
                    ),
                    # Plots
                    ui.row(
                        ui.column(4, 
                            ui.div(
                                ui.h4("Clinical Assessment Distribution", style="margin-bottom: 15px; color: #2c3e50;"),
                                ui.output_plot("assessment_pie", height="400px"),
                                style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"
                            )
                        ),
                        ui.column(4, 
                            ui.div(
                                ui.h4("Top 10 Mutated Genes", style="margin-bottom: 15px; color: #2c3e50;"),
                                ui.output_plot("gene_bar", height="400px"),
                                style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"
                            )
                        ),
                        ui.column(4, 
                            ui.div(
                                ui.h4("Allele Fraction Distribution", style="margin-bottom: 15px; color: #2c3e50;"),
                                ui.output_plot("allele_fraction_hist", height="400px"),
                                style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"
                            )
                        ),
                        style="margin-top: 20px;"
                    ),
                    # Oncoprint on full width for better visibility
                    ui.row(
                        ui.column(12, 
                            ui.div(
                                ui.h4("Mutation Landscape", style="margin-bottom: 15px; color: #2c3e50;"),
                                ui.output_plot("oncoprint", height="500px"),
                                style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"
                            )
                        ),
                        style="margin-top: 20px;"
                    )
                )
            ),
            
            # ═══════════════════════════════════════════════════════════════
            # CLINICAL TRIAL PARTICIPATION TAB
            # ═══════════════════════════════════════════════════════════════
            ui.nav_panel(
                "Clinical Trial Participation",
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.div(
                            ui.h4("Clinical Trial Filters"),
                            ui.input_selectize(
                                "protocol_filter",
                                "Protocol:",
                                choices=["All"] + sorted(data['protocols']['protocol_id'].unique().tolist()),
                                selected="All",
                                multiple=False
                            ),
                            ui.input_selectize(
                                "intervention_filter",
                                "Intervention Type:",
                                choices=["All"] + sorted(data['interventions']['intervention_category'].unique().tolist()),
                                selected="All",
                                multiple=False
                            ),
                            ui.input_checkbox_group(
                                "adverse_event_filter",
                                "Adverse Event Grade:",
                                choices={
                                    "1": "Grade 1",
                                    "2": "Grade 2", 
                                    "3": "Grade 3",
                                    "4": "Grade 4",
                                    "5": "Grade 5"
                                },
                                selected=["1", "2", "3", "4", "5"]
                            ),
                            class_="filter-section"
                        ),
                        width=300
                    ),
                    # Summary cards
                    ui.row(
                        ui.column(3, ui.output_ui("total_protocols_card")),
                        ui.column(3, ui.output_ui("enrolled_patients_card")),
                        ui.column(3, ui.output_ui("total_interventions_card")),
                        ui.column(3, ui.output_ui("serious_ae_card"))
                    ),
                    # Clinical trial visualizations
                    ui.row(
                        ui.column(6, 
                            ui.div(
                                ui.h4("Protocol Enrollment", style="margin-bottom: 15px; color: #2c3e50;"),
                                ui.output_plot("protocol_enrollment", height="450px"),
                                style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"
                            )
                        ),
                        ui.column(6, 
                            ui.div(
                                ui.h4("Intervention Distribution", style="margin-bottom: 15px; color: #2c3e50;"),
                                ui.output_plot("intervention_dist", height="450px"),
                                style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"
                            )
                        ),
                        style="margin-top: 20px;"
                    ),
                    ui.row(
                        ui.column(6, 
                            ui.div(
                                ui.h4("Adverse Events by Grade", style="margin-bottom: 15px; color: #2c3e50;"),
                                ui.output_plot("ae_grade_dist", height="450px"),
                                style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"
                            )
                        ),
                        ui.column(6, 
                            ui.div(
                                ui.h4("Adverse Events by System", style="margin-bottom: 15px; color: #2c3e50;"),
                                ui.output_plot("ae_system_dist", height="450px"),
                                style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"
                            )
                        ),
                        style="margin-top: 20px;"
                    )
                )
            ),
            
            # ═══════════════════════════════════════════════════════════════
            # OUTCOMES TAB
            # ═══════════════════════════════════════════════════════════════
            ui.nav_panel(
                "Outcomes",
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.div(
                            ui.h4("Outcomes Analysis"),
                            ui.p("Survival analysis based on intervention types and patient characteristics."),
                            ui.input_selectize(
                                "survival_stratify",
                                "Stratify by:",
                                choices={
                                    "intervention": "Intervention Type",
                                    "protocol": "Protocol",
                                    "gene": "Gene Mutation",
                                    "sex": "Sex"
                                },
                                selected="intervention"
                            ),
                            class_="filter-section"
                        ),
                        width=300
                    ),
                    ui.row(
                        ui.column(12, 
                            ui.div(
                                ui.h4("Kaplan-Meier Survival Analysis", style="margin-bottom: 15px; color: #2c3e50;"),
                                ui.output_plot("survival_curve", height="500px"),
                                style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"
                            )
                        )
                    ),
                    ui.row(
                        ui.column(12, 
                            ui.h4("Outcomes Summary", style="margin-top: 20px;"),
                            ui.output_ui("outcomes_summary")
                        )
                    )
                )
            )
        ),
        style="padding: 0 30px 30px 30px;"
    )
)

# ═══════════════════════════════════════════════════════════════
# SERVER LOGIC
# ═══════════════════════════════════════════════════════════════

def server(input: Inputs, output: Outputs, session: Session):
    
    # ═══════════════════════════════════════════════════════════════
    # REACTIVE DATA FILTERING
    # ═══════════════════════════════════════════════════════════════
    
    @reactive.Calc
    def filtered_data():
        """Apply filters to the merged dataframe"""
        # Start with all merged data
        filtered_df = data['merged'].copy()
        
        # Only apply filters if they're actually changed from defaults
        # Demographics filters
        if len(input.demo_sex_filter()) < 2:  # If not both selected
            filtered_df = filtered_df[filtered_df['sex'].isin(input.demo_sex_filter())]
            
        # Age filter
        age_range = input.demo_age_filter()
        if age_range[0] > 18 or age_range[1] < 85:  # If changed from default
            filtered_df = filtered_df[
                (filtered_df['age'] >= age_range[0]) & 
                (filtered_df['age'] <= age_range[1])
            ]
        
        # Gene filter
        if input.gene_filter() != "All":
            filtered_df = filtered_df[filtered_df['gene'] == input.gene_filter()]
            
        # Assessment filter
        if len(input.assessment_filter()) < 5:  # If not all selected
            filtered_df = filtered_df[filtered_df['assessment'].isin(input.assessment_filter())]
            
        return filtered_df
    
    @output
    @render.plot(alt="Age Distribution")
    def age_distribution():
        plt.close('all')  # Close any existing figures
        fig, ax = plt.subplots(figsize=(8, 5), tight_layout=True)
        df = filtered_data()
        
        unique_patients = df.drop_duplicates('mrn')
        
        # Professional blue color
        ax.hist(unique_patients['age'], bins=20, color='#0068B1', 
                alpha=0.8, edgecolor='white', linewidth=1.2)
        
        # Add mean line
        mean_age = unique_patients['age'].mean()
        ax.axvline(mean_age, color='#E83E48', linestyle='--', linewidth=2.5, alpha=0.8)
        ax.text(mean_age + 1, ax.get_ylim()[1] * 0.9, f'Mean: {mean_age:.1f}', 
                color='#E83E48', fontweight='600', fontsize=11)
        
        ax.set_xlabel('Age', fontsize=12, fontweight='500')
        ax.set_ylabel('Number of Patients', fontsize=12, fontweight='500')
        ax.grid(True, alpha=0.2)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout(pad=2.0)
        return fig
    
    @output
    @render.plot(alt="Sex Distribution")
    def sex_distribution():
        plt.close('all')
        fig, ax = plt.subplots(figsize=(8, 5), tight_layout=True)
        df = filtered_data()
        
        unique_patients = df.drop_duplicates('mrn')
        sex_counts = unique_patients['sex'].value_counts()
        
        colors = ['#0068B1', '#E83E48']
        bars = ax.bar(sex_counts.index, sex_counts.values, color=colors, alpha=0.7, edgecolor='black')
        ax.set_xlabel('Sex', fontsize=12)
        ax.set_ylabel('Number of Patients', fontsize=12)
        
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for i, v in enumerate(sex_counts.values):
            ax.text(i, v + 1, str(v), ha='center', fontweight='bold')
        
        plt.tight_layout(pad=2.0)
        return fig
    
    @output
    @render.ui
    def demographics_summary():
        df = filtered_data()
        unique_patients = df.drop_duplicates('mrn')
        
        return ui.div(
            ui.p(f"Total Patients: {len(unique_patients)}", style="font-size: 16px;"),
            ui.p(f"Average Age: {unique_patients['age'].mean():.1f} years", style="font-size: 16px;"),
            ui.p(f"Age Range: {unique_patients['age'].min()} - {unique_patients['age'].max()} years", style="font-size: 16px;"),
            style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"
        )
    
    # ═══════════════════════════════════════════════════════════════
    # GENOMICS TAB OUTPUTS
    # ═══════════════════════════════════════════════════════════════
    
    @output
    @render.ui
    def total_variants_card():
        df = filtered_data()
        return summary_card("Total Variants", len(df), "🧬")
    
    @output
    @render.ui
    def unique_genes_card():
        df = filtered_data()
        return summary_card("Unique Genes", df['gene'].nunique(), "🧬")
    
    @output
    @render.ui
    def pathogenic_count_card():
        df = filtered_data()
        pathogenic = df[df['assessment'].isin(['Pathogenic', 'Likely Pathogenic'])]
        return summary_card("Pathogenic", len(pathogenic), "⚠️")
    
    @output
    @render.ui
    def actionable_count_card():
        df = filtered_data()
        actionable = df[df['actionability'].notna() & (df['actionability'] != '')]
        return summary_card("Actionable", len(actionable), "💊")
    
    @output
    @render.plot(alt="Clinical Assessment Distribution")
    def assessment_pie():
        plt.close('all')
        fig, ax = plt.subplots(figsize=(6, 5), tight_layout=True)
        df = filtered_data()
        
        assessment_counts = df['assessment'].value_counts()
        colors = ['#E83E48', '#FF9800', '#6C757D', '#1881C2', '#00A783']
        
        wedges, texts, autotexts = ax.pie(assessment_counts.values, 
                                           labels=assessment_counts.index, 
                                           autopct='%1.1f%%',
                                           colors=colors, 
                                           startangle=90,
                                           textprops={'fontsize': 8})
        
        # Adjust text sizes
        for text in texts:
            text.set_fontsize(9)
        for autotext in autotexts:
            autotext.set_fontsize(8)
            autotext.set_color('white')
            autotext.set_weight('bold')
        
        plt.tight_layout(pad=2.0)
        return fig
    
    @output
    @render.plot(alt="Top 10 Mutated Genes")
    def gene_bar():
        plt.close('all')
        fig, ax = plt.subplots(figsize=(7, 5))
        df = filtered_data()
        
        top_genes = df['gene'].value_counts().head(10)
        ax.barh(top_genes.index[::-1], top_genes.values[::-1], color='#0068B1', alpha=0.7)
        ax.set_xlabel('Number of Variants', fontsize=11)
        ax.tick_params(axis='y', labelsize=9)
        
        ax.grid(True, alpha=0.3, axis='x')
        
        # Use tight_layout with extra padding on the left
        plt.tight_layout()
        plt.subplots_adjust(left=0.3)
        return fig
    
    @output
    @render.plot
    def allele_fraction_hist():
        fig, ax = plt.subplots(figsize=(7, 6))
        df = filtered_data()
        
        ax.hist(df['allelefraction'], bins=30, color='#00A783', alpha=0.7, edgecolor='black')
        ax.set_xlabel('Allele Fraction', fontsize=11)
        ax.set_ylabel('Count', fontsize=11)
        
        ax.grid(True, alpha=0.3)
        
        fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.15)
        return fig
    
    @output
    @render.plot(alt="Mutation Landscape")
    def oncoprint():
        """Create a simplified oncoprint visualization"""
        plt.close('all')
        fig, ax = plt.subplots(figsize=(12, 5))
        df = filtered_data()
        
        # Get top genes and sample of patients
        top_genes = df['gene'].value_counts().head(10).index
        gene_data = df[df['gene'].isin(top_genes)]
        
        # Create matrix
        patients = gene_data['mrn'].unique()[:25]  # Show patients
        
        # Create color map for assessments
        color_map = {
            'Pathogenic': '#e74c3c',
            'Likely Pathogenic': '#f39c12',
            'VUS': '#95a5a6',
            'Likely Benign': '#3498db',
            'Benign': '#2ecc71'
        }
        
        # Plot
        y_pos = 0
        for gene in top_genes:
            x_pos = 0
            for patient in patients:
                patient_gene = gene_data[(gene_data['mrn'] == patient) & (gene_data['gene'] == gene)]
                if not patient_gene.empty:
                    assessment = patient_gene.iloc[0]['assessment']
                    color = color_map.get(assessment, 'gray')
                    rect = Rectangle((x_pos, y_pos), 1, 1, facecolor=color, edgecolor='black', linewidth=0.5)
                    ax.add_patch(rect)
                x_pos += 1
            y_pos += 1
        
        ax.set_xlim(0, len(patients))
        ax.set_ylim(0, len(top_genes))
        ax.set_xticks(range(len(patients)))
        ax.set_xticklabels([f"P{i+1}" for i in range(len(patients))], rotation=45, ha='right', fontsize=8)
        ax.set_yticks(range(len(top_genes)))
        ax.set_yticklabels(top_genes, fontsize=10)
        
        ax.set_xlabel('Patients', fontsize=12)
        ax.set_ylabel('Genes', fontsize=12)
        
        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor=color, label=assessment) 
                          for assessment, color in color_map.items()]
        
        ax.legend(handles=legend_elements, 
                 loc='center left', 
                 bbox_to_anchor=(1.02, 0.5),
                 fontsize=9,
                 title='Assessment',
                 frameon=True)
        
        # Adjust layout
        plt.tight_layout()
        plt.subplots_adjust(right=0.82, bottom=0.15)
        return fig
    
    # ═══════════════════════════════════════════════════════════════
    # CLINICAL TRIAL PARTICIPATION TAB OUTPUTS
    # ═══════════════════════════════════════════════════════════════
    
    @output
    @render.ui
    def total_protocols_card():
        return summary_card("Active Protocols", len(data['protocols']), "🏥")
    
    @output
    @render.ui
    def enrolled_patients_card():
        df = filtered_data()
        enrolled = len(df['mrn'].unique())
        return summary_card("Enrolled Patients", enrolled, "👥")
    
    @output
    @render.ui
    def total_interventions_card():
        return summary_card("Intervention Types", len(data['interventions']['intervention_category'].unique()), "💊")
    
    @output
    @render.ui
    def serious_ae_card():
        serious_ae = data['adverse_events'][data['adverse_events']['serious'] == True]
        return summary_card("Serious AEs", len(serious_ae), "⚠️")
    
    @output
    @render.plot(alt="Protocol Enrollment")
    def protocol_enrollment():
        plt.close('all')
        fig, ax = plt.subplots(figsize=(9, 5))
        
        # Count enrollments per protocol
        protocol_counts = data['subjects']['protocol_id'].value_counts()
        
        ax.bar(range(len(protocol_counts)), protocol_counts.values, color='#0068B1', alpha=0.7)
        ax.set_xlabel('Protocol', fontsize=12)
        ax.set_ylabel('Number of Patients', fontsize=12)
        
        ax.set_xticks(range(len(protocol_counts)))
        ax.set_xticklabels(protocol_counts.index, rotation=45, ha='right', fontsize=9)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Ensure labels don't get cut off
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.2)
        return fig
    
    @output
    @render.plot
    def intervention_dist():
        fig, ax = plt.subplots(figsize=(10, 7))
        
        intervention_counts = data['interventions']['intervention_category'].value_counts()
        
        # Shorter labels with better formatting
        labels = []
        for i in intervention_counts.index[::-1]:
            label = i.replace(' Therapy', '')
            label = label.replace('Angiogenesis Inhibitors', 'Angiogenesis Inh.')
            label = label.replace('Immunotherapy', 'Immuno')
            label = label.replace('Chemotherapy', 'Chemo')
            labels.append(label)
        
        ax.barh(range(len(intervention_counts)), intervention_counts.values[::-1], 
                color='#00A783', alpha=0.7)
        
        ax.set_yticks(range(len(intervention_counts)))
        ax.set_yticklabels(labels, fontsize=10, fontweight='500')
        ax.set_xlabel('Number of Patients', fontsize=12)
        
        ax.grid(True, alpha=0.3, axis='x')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Increased left margin to prevent label cutoff
        plt.tight_layout(rect=[0.18, 0, 1, 1])
        return fig
    
    @output
    @render.plot
    def ae_grade_dist():
        fig, ax = plt.subplots(figsize=(9, 6))
        
        grade_counts = data['adverse_events']['grade'].value_counts().sort_index()
        
        colors = ['#00A783', '#1881C2', '#FF9800', '#E83E48', '#8B0000']
        ax.bar(grade_counts.index, grade_counts.values, 
               color=[colors[i-1] for i in grade_counts.index], alpha=0.7)
        ax.set_xlabel('Grade', fontsize=12)
        ax.set_ylabel('Number of Events', fontsize=12)
        
        ax.grid(True, alpha=0.3, axis='y')
        
        # Ensure proper layout
        fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.1)
        return fig
    
    @output
    @render.plot
    def ae_system_dist():
        fig, ax = plt.subplots(figsize=(10, 7))
        
        system_counts = data['adverse_events']['ae_body_system'].value_counts().head(8)
        
        # Much shorter labels
        label_map = {
            'Respiratory, thoracic and mediastinal disorders': 'Respiratory',
            'Blood and lymphatic system disorders': 'Blood/Lymph',
            'Cardiac disorders': 'Cardiac',
            'Gastrointestinal disorders': 'GI',
            'General disorders and administration site conditions': 'General',
            'Hepatobiliary disorders': 'Hepatobiliary',
            'Immune system disorders': 'Immune',
            'Infections and infestations': 'Infections',
            'Metabolism and nutrition disorders': 'Metabolism',
            'Musculoskeletal and connective tissue disorders': 'Musculoskeletal',
            'Nervous system disorders': 'Nervous',
            'Skin and subcutaneous tissue disorders': 'Skin'
        }
        
        labels = [label_map.get(x, x.split()[0][:12]) for x in system_counts.index]
        
        # Use gradient colors
        colors = ['#E57373', '#EF5350', '#F44336', '#E53935', '#D32F2F', '#C62828', '#B71C1C', '#D50000']
        
        bars = ax.barh(range(len(system_counts)), system_counts.values, 
                       color=colors[:len(system_counts)], edgecolor='white', linewidth=1.5)
        
        # Add values
        for i, v in enumerate(system_counts.values):
            ax.text(v + 1, i, str(v), va='center', fontweight='500')
        
        ax.set_yticks(range(len(system_counts)))
        ax.set_yticklabels(labels, fontsize=10, fontweight='500')
        ax.set_xlabel('Number of Events', fontsize=12, fontweight='500')
        ax.grid(True, alpha=0.2, axis='x')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.invert_yaxis()
        
        # Adjust margins - increased left margin
        plt.subplots_adjust(left=0.3)
        plt.tight_layout()
        return fig
    
    @output
    @render.plot
    def survival_curve():
        """Generate Kaplan-Meier survival curves"""
        fig, ax = plt.subplots(figsize=(10, 7))
        
        from lifelines import KaplanMeierFitter
        
        # Set seed for reproducibility
        np.random.seed(42)
        
        stratify_by = input.survival_stratify()
        
        # Get filtered patient data
        df = filtered_data()
        
        if stratify_by == "intervention":
            # Load intervention data from CSV
            try:
                subjects_df = pd.read_csv('clinical_trial_subjects.csv')
                interventions_df = pd.read_csv('interventions.csv')
                
                # Get unique interventions
                intervention_types = interventions_df['intervention_category'].unique()[:4]
                
                for intervention in intervention_types:
                    # Get patients with this intervention
                    intervention_raves = interventions_df[
                        interventions_df['intervention_category'] == intervention
                    ]['rave_id'].unique()
                    
                    intervention_mrns = subjects_df[
                        subjects_df['rave_id'].isin(intervention_raves)
                    ]['mrn'].unique()
                    
                    # Filter to patients in our current dataset
                    intervention_patients = df[df['mrn'].isin(intervention_mrns)]['mrn'].unique()
                    n_patients = len(intervention_patients)
                    
                    if n_patients > 0:
                        # Generate synthetic survival data based on intervention type
                        if intervention == "Immunotherapy":
                            times = np.random.exponential(scale=500, size=n_patients)
                            events = np.random.binomial(1, 0.6, size=n_patients)
                        elif intervention == "Chemotherapy":
                            times = np.random.exponential(scale=400, size=n_patients)
                            events = np.random.binomial(1, 0.7, size=n_patients)
                        elif intervention == "Targeted Therapy":
                            times = np.random.exponential(scale=450, size=n_patients)
                            events = np.random.binomial(1, 0.65, size=n_patients)
                        else:
                            times = np.random.exponential(scale=350, size=n_patients)
                            events = np.random.binomial(1, 0.75, size=n_patients)
                        
                        # Fit and plot
                        kmf = KaplanMeierFitter()
                        kmf.fit(times, events, label=f"{intervention} (n={n_patients})")
                        kmf.plot_survival_function(ax=ax)
                        
            except Exception as e:
                print(f"Error loading intervention data: {e}")
        
        elif stratify_by == "protocol":
            # Load protocol data from CSV
            try:
                subjects_df = pd.read_csv('clinical_trial_subjects.csv')
                protocols_df = pd.read_csv('protocols.csv')
                
                # Get protocol enrollment counts
                protocol_counts = subjects_df['protocol_id'].value_counts().head(4)
                
                for protocol_id in protocol_counts.index:
                    # Get patients in this protocol
                    protocol_mrns = subjects_df[
                        subjects_df['protocol_id'] == protocol_id
                    ]['mrn'].unique()
                    
                    # Filter to patients in our current dataset
                    protocol_patients = df[df['mrn'].isin(protocol_mrns)]['mrn'].unique()
                    n_patients = len(protocol_patients)
                    
                    if n_patients > 0:
                        # Get phase information
                        phase = protocols_df[
                            protocols_df['protocol_id'] == protocol_id
                        ]['phase'].iloc[0] if len(protocols_df[protocols_df['protocol_id'] == protocol_id]) > 0 else "Unknown"
                        
                        # Generate synthetic survival data based on phase
                        if phase == "Phase III":
                            times = np.random.exponential(scale=500, size=n_patients)
                            events = np.random.binomial(1, 0.6, size=n_patients)
                        elif phase == "Phase II":
                            times = np.random.exponential(scale=400, size=n_patients)
                            events = np.random.binomial(1, 0.7, size=n_patients)
                        else:  # Phase I
                            times = np.random.exponential(scale=300, size=n_patients)
                            events = np.random.binomial(1, 0.8, size=n_patients)
                        
                        # Fit and plot
                        kmf = KaplanMeierFitter()
                        kmf.fit(times, events, label=f"{protocol_id} - {phase} (n={n_patients})")
                        kmf.plot_survival_function(ax=ax)
                        
            except Exception as e:
                print(f"Error loading protocol data: {e}")
        
        elif stratify_by == "gene":
            # Get top mutated genes from filtered data
            top_genes = df['gene'].value_counts().head(4).index
            
            for gene in top_genes:
                # Get patients with this gene mutation
                gene_patients = df[df['gene'] == gene]['mrn'].unique()
                n_patients = len(gene_patients)
                
                if n_patients > 0:
                    # Generate synthetic survival data based on gene
                    if gene in ['TP53', 'KRAS']:
                        times = np.random.exponential(scale=350, size=n_patients)
                        events = np.random.binomial(1, 0.75, size=n_patients)
                    elif gene in ['BRCA1', 'BRCA2']:
                        times = np.random.exponential(scale=500, size=n_patients)
                        events = np.random.binomial(1, 0.6, size=n_patients)
                    else:
                        times = np.random.exponential(scale=450, size=n_patients)
                        events = np.random.binomial(1, 0.65, size=n_patients)
                    
                    # Fit and plot
                    kmf = KaplanMeierFitter()
                    kmf.fit(times, events, label=f"{gene} mutation (n={n_patients})")
                    kmf.plot_survival_function(ax=ax)
        
        elif stratify_by == "sex":
            # Stratify by sex - this should work since it's in the filtered data
            unique_patients = df.drop_duplicates('mrn')
            
            for sex in ['male', 'female']:
                sex_patients = unique_patients[unique_patients['sex'] == sex]['mrn'].values
                n_patients = len(sex_patients)
                
                if n_patients > 0:
                    # Generate synthetic survival data
                    if sex == 'female':
                        times = np.random.exponential(scale=480, size=n_patients)
                        events = np.random.binomial(1, 0.65, size=n_patients)
                    else:
                        times = np.random.exponential(scale=420, size=n_patients)
                        events = np.random.binomial(1, 0.7, size=n_patients)
                    
                    # Fit and plot
                    kmf = KaplanMeierFitter()
                    kmf.fit(times, events, label=f"{sex.capitalize()} (n={n_patients})")
                    kmf.plot_survival_function(ax=ax)
        
        # Customize plot
        ax.set_xlabel('Time (days)', fontsize=12)
        ax.set_ylabel('Survival Probability', fontsize=12)
        
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best', fontsize=10)
        
        # Add median survival line
        ax.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5)
        
        # Ensure proper layout
        fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.15)
        return fig
    
    @output
    @render.ui
    def outcomes_summary():
        """Generate outcomes summary statistics"""
        df = filtered_data()
        unique_patients = df.drop_duplicates('mrn')
        
        # Get clinical trial data
        enrolled_patients = data['subjects']['mrn'].nunique()
        completed_trials = len(data['subjects'][data['subjects']['enrollment_status'] == 'Completed'])
        
        return ui.div(
            ui.h5("Clinical Trial Outcomes", style="margin-bottom: 15px;"),
            ui.p(f"Total Enrolled Patients: {enrolled_patients}", style="font-size: 16px;"),
            ui.p(f"Completed Enrollments: {completed_trials}", style="font-size: 16px;"),
            ui.p(f"Active Enrollments: {len(data['subjects'][data['subjects']['enrollment_status'] == 'Active'])}", style="font-size: 16px;"),
            ui.p(f"Withdrawal Rate: {len(data['subjects'][data['subjects']['enrollment_status'] == 'Withdrawn']) / len(data['subjects']) * 100:.1f}%", style="font-size: 16px;"),
            style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"
        )

# Create the app
app = App(app_ui, server)