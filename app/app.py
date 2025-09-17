import os
import sys
import streamlit as st
import csv
import json
import base64
from datetime import datetime, timedelta

# Set up import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

try:
    from agents.flavorbot import run_flavorbot
except ImportError:
    st.error("FlavorBot module not found. Please ensure the agents/flavorbot module is properly installed.")
    st.stop()

# --------------------------
# ENTERPRISE DATA MANAGEMENT
# --------------------------
def load_user_preferences():
    """Load user preferences and settings."""
    try:
        if os.path.exists("user_preferences.json"):
            with open("user_preferences.json", "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {
        "theme": "light",
        "dietary_restrictions": [],
        "cooking_skill": "intermediate",
        "favorite_cuisines": [],
        "preferred_meal_times": {},
        "notification_settings": {},
        "language": "en"
    }

def save_user_preferences(prefs):
    """Save user preferences."""
    try:
        with open("user_preferences.json", "w", encoding="utf-8") as f:
            json.dump(prefs, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Error saving preferences: {e}")
        return False

def load_analytics_data():
    """Load analytics data for dashboard."""
    try:
        if os.path.exists("analytics_data.json"):
            with open("analytics_data.json", "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {
        "daily_interactions": [],
        "recipe_categories": {},
        "user_satisfaction": [],
        "feature_usage": {},
        "session_duration": []
    }

def update_analytics(action_type, value=1):
    """Update analytics data."""
    analytics = load_analytics_data()
    today = datetime.now().strftime("%Y-%m-%d")

    # Update based on action type
    if action_type == "recipe_request":
        analytics["daily_interactions"].append({"date": today, "type": "recipe", "count": value})
    elif action_type == "bookmark":
        analytics["feature_usage"]["bookmarks"] = analytics["feature_usage"].get("bookmarks", 0) + 1
    elif action_type == "shopping_list":
        analytics["feature_usage"]["shopping"] = analytics["feature_usage"].get("shopping", 0) + 1

    # Keep only last 30 days
    cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    analytics["daily_interactions"] = [d for d in analytics["daily_interactions"] if d.get("date", "") >= cutoff_date]

    try:
        with open("analytics_data.json", "w", encoding="utf-8") as f:
            json.dump(analytics, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def load_bookmarks():
    """Load bookmarks from JSON file."""
    try:
        if os.path.exists("bookmarks.json"):
            with open("bookmarks.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                # Ensure all bookmarks are dictionaries
                if isinstance(data, list):
                    return [item for item in data if isinstance(item, dict)]
                return []
    except Exception as e:
        st.error(f"Error loading bookmarks: {e}")
    return []

def save_bookmarks(bookmarks):
    """Save bookmarks to JSON file."""
    try:
        with open("bookmarks.json", "w", encoding="utf-8") as f:
            json.dump(bookmarks, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Error saving bookmarks: {e}")
        return False

def add_bookmark(recipe_text, query, rating=None, tags=None):
    """Add a recipe to bookmarks."""
    bookmarks = load_bookmarks()
    bookmark = {
        "id": len(bookmarks) + 1,
        "query": query,
        "recipe": recipe_text,
        "timestamp": datetime.now().isoformat(),
        "rating": rating,
        "tags": tags or [],
        "cook_count": 0,
        "prep_time": None,
        "difficulty": None
    }
    bookmarks.append(bookmark)
    update_analytics("bookmark")
    return save_bookmarks(bookmarks)

def rate_bookmark(bookmark_id, rating):
    """Rate a bookmarked recipe."""
    bookmarks = load_bookmarks()
    for bookmark in bookmarks:
        if isinstance(bookmark, dict) and bookmark.get("id") == bookmark_id:
            bookmark["rating"] = rating
            break
    return save_bookmarks(bookmarks)

def remove_bookmark(bookmark_id):
    """Remove a bookmark by ID."""
    bookmarks = load_bookmarks()
    bookmarks = [b for b in bookmarks if isinstance(b, dict) and b.get("id") != bookmark_id]
    return save_bookmarks(bookmarks)

def load_shopping_list():
    """Load shopping list from JSON file."""
    try:
        if os.path.exists("shopping_list.json"):
            with open("shopping_list.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                # Ensure all items are properly formatted
                if isinstance(data, list):
                    return data
                return []
    except Exception as e:
        st.error(f"Error loading shopping list: {e}")
    return []

def save_shopping_list(items):
    """Save shopping list to JSON file."""
    try:
        with open("shopping_list.json", "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Error saving shopping list: {e}")
        return False

def add_to_shopping_list(ingredients):
    """Add ingredients to shopping list."""
    shopping_list = load_shopping_list()
    for ingredient in ingredients:
        ingredient_text = ingredient if isinstance(ingredient, str) else str(ingredient)
        # Check if ingredient already exists
        existing_items = [item.get('item', '') if isinstance(item, dict) else str(item) for item in shopping_list]
        if ingredient_text not in existing_items:
            shopping_list.append({
                "item": ingredient_text,
                "added": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "checked": False
            })
    return save_shopping_list(shopping_list)

def extract_ingredients_from_recipe(recipe_text):
    """Simple ingredient extraction from recipe text."""
    import re
    lines = recipe_text.split('\n')
    ingredients = []

    # Look for ingredient sections
    in_ingredients = False
    for line in lines:
        line = line.strip()
        if any(word in line.lower() for word in ['ingredient', 'you need', 'required']):
            in_ingredients = True
            continue
        elif any(word in line.lower() for word in ['instruction', 'direction', 'step', 'method']):
            in_ingredients = False

        if in_ingredients and line and not line.startswith('#'):
            # Clean up ingredient line
            ingredient = re.sub(r'^[-•*]\s*', '', line)  # Remove bullets
            ingredient = re.sub(r'\d+\.\s*', '', ingredient)  # Remove numbers
            if len(ingredient) > 3 and len(ingredient) < 100:
                ingredients.append(ingredient)

    return ingredients[:10]  # Limit to 10 ingredients

def get_base64_of_image(path):
    """Convert image to base64 string."""
    try:
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        return None

def apply_enterprise_styling(theme="light"):
    """Apply enterprise-grade styling."""

    # Enterprise color palette
    if theme == "dark":
        colors = {
            "primary": "#0066CC",
            "secondary": "#004499", 
            "success": "#00AA44",
            "warning": "#FF8800",
            "danger": "#CC0000",
            "bg_primary": "#1A1D23",
            "bg_secondary": "#252A34", 
            "bg_tertiary": "#2F3542",
            "text_primary": "#FFFFFF",
            "text_secondary": "#B8BCC8",
            "text_muted": "#8B8FA3",
            "border": "#404651",
            "shadow": "rgba(0, 0, 0, 0.3)"
        }
    else:
        colors = {
            "primary": "#0066CC",
            "secondary": "#004499",
            "success": "#00AA44", 
            "warning": "#FF8800",
            "danger": "#CC0000",
            "bg_primary": "#FFFFFF",
            "bg_secondary": "#F8F9FA",
            "bg_tertiary": "#F1F3F6",
            "text_primary": "#2C3E50",
            "text_secondary": "#5A6C7D",
            "text_muted": "#8B98A9",
            "border": "#E1E8ED",
            "shadow": "rgba(0, 0, 0, 0.1)"
        }

    bg_image = get_base64_of_image("background2.png")
    bg_style = f'background: url("data:image/png;base64,{bg_image}") no-repeat center center fixed; background-size: cover;' if bg_image else f"background: linear-gradient(135deg, {colors['bg_secondary']} 0%, {colors['bg_tertiary']} 100%);"

    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    :root {{
        --primary: {colors['primary']};
        --secondary: {colors['secondary']};
        --success: {colors['success']};
        --warning: {colors['warning']};
        --danger: {colors['danger']};
        --bg-primary: {colors['bg_primary']};
        --bg-secondary: {colors['bg_secondary']};
        --bg-tertiary: {colors['bg_tertiary']};
        --text-primary: {colors['text_primary']};
        --text-secondary: {colors['text_secondary']};
        --text-muted: {colors['text_muted']};
        --border: {colors['border']};
        --shadow: {colors['shadow']};
        --border-radius: 12px;
        --border-radius-lg: 16px;
        --spacing-sm: 0.5rem;
        --spacing-md: 1rem;
        --spacing-lg: 1.5rem;
        --spacing-xl: 2rem;
        --font-size-sm: 0.875rem;
        --font-size-base: 1rem;
        --font-size-lg: 1.125rem;
        --font-size-xl: 1.25rem;
        --font-weight-normal: 400;
        --font-weight-medium: 500;
        --font-weight-semibold: 600;
        --font-weight-bold: 700;
        --transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }}

    .stApp {{
        {bg_style}
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size: var(--font-size-base);
        line-height: 1.6;
        color: var(--text-primary);
    }}

    /* ENTERPRISE HEADER */
    .enterprise-header {{
        background: var(--bg-primary);
        border-bottom: 1px solid var(--border);
        padding: var(--spacing-md) var(--spacing-xl);
        box-shadow: 0 2px 4px var(--shadow);
        position: sticky;
        top: 0;
        z-index: 1000;
        backdrop-filter: blur(10px);
    }}

    .header-content {{
        max-width: 1400px;
        margin: 0 auto;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}

    .logo-section {{
        display: flex;
        align-items: center;
        gap: var(--spacing-md);
    }}

    .company-logo {{
        font-size: 1.5rem;
        font-weight: var(--font-weight-bold);
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}

    .user-actions {{
        display: flex;
        align-items: center;
        gap: var(--spacing-md);
    }}

    /* MAIN CONTENT AREA */
    .main .block-container {{
        max-width: 1400px;
        padding: var(--spacing-xl);
        background: var(--bg-primary);
        border-radius: var(--border-radius-lg);
        box-shadow: 0 4px 6px -1px var(--shadow), 0 2px 4px -1px var(--shadow);
        margin: var(--spacing-lg) auto;
        border: 1px solid var(--border);
    }}

    /* ENTERPRISE CARDS */
    .enterprise-card {{
        background: var(--bg-primary);
        border: 1px solid var(--border);
        border-radius: var(--border-radius);
        padding: var(--spacing-lg);
        box-shadow: 0 1px 3px var(--shadow);
        transition: var(--transition);
        margin: var(--spacing-md) 0;
    }}

    .enterprise-card:hover {{
        box-shadow: 0 4px 6px -1px var(--shadow), 0 2px 4px -1px var(--shadow);
        transform: translateY(-1px);
    }}

    .card-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: var(--spacing-md);
        padding-bottom: var(--spacing-sm);
        border-bottom: 1px solid var(--border);
    }}

    .card-title {{
        font-size: var(--font-size-lg);
        font-weight: var(--font-weight-semibold);
        color: var(--text-primary);
        margin: 0;
    }}

    .card-subtitle {{
        color: var(--text-muted);
        font-size: var(--font-size-sm);
        margin: 0;
    }}

    /* SIDEBAR */
    section[data-testid="stSidebar"] {{
        background: var(--bg-secondary);
        border-right: 1px solid var(--border);
        box-shadow: 2px 0 4px var(--shadow);
    }}

    section[data-testid="stSidebar"] .stMarkdown {{
        color: var(--text-primary);
    }}

    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] h4 {{
        color: var(--text-primary);
    }}

    /* CHAT INTERFACE */
    .stChatMessage {{
        background: var(--bg-primary);
        border: 1px solid var(--border);
        border-radius: var(--border-radius);
        padding: var(--spacing-lg);
        margin: var(--spacing-lg) 0;
        box-shadow: 0 1px 3px var(--shadow);
        transition: var(--transition);
    }}

    .stChatMessage:hover {{
        box-shadow: 0 4px 6px -1px var(--shadow);
        transform: translateY(-1px);
    }}

    .stChatMessage .stMarkdown {{
        color: var(--text-primary);
    }}

    .stChatMessage p {{
        color: var(--text-secondary);
        line-height: 1.7;
        margin-bottom: var(--spacing-sm);
    }}

    /* CHAT INPUT */
    .stChatInput > div {{
        background: var(--bg-primary);
        border: 2px solid var(--border);
        border-radius: var(--border-radius);
        box-shadow: 0 1px 3px var(--shadow);
        transition: var(--transition);
    }}

    .stChatInput > div:focus-within {{
        border-color: var(--primary);
        box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.1);
    }}

    .stChatInput input {{
        color: var(--text-primary);
        font-size: var(--font-size-base);
    }}

    .stChatInput input::placeholder {{
        color: var(--text-muted);
    }}

    /* FORMS */
    .stSelectbox > div > div {{
        background: var(--bg-primary);
        border: 1px solid var(--border);
        border-radius: var(--border-radius);
        color: var(--text-primary);
    }}

    .stButton > button {{
        background: var(--primary);
        color: white;
        border: 1px solid var(--primary);
        border-radius: var(--border-radius);
        padding: var(--spacing-sm) var(--spacing-lg);
        font-weight: var(--font-weight-medium);
        transition: var(--transition);
    }}

    .stButton > button:hover {{
        background: var(--secondary);
        border-color: var(--secondary);
        transform: translateY(-1px);
        box-shadow: 0 4px 6px var(--shadow);
    }}

    /* METRICS & KPIs */
    .metric-card {{
        background: var(--bg-primary);
        border: 1px solid var(--border);
        border-radius: var(--border-radius);
        padding: var(--spacing-lg);
        text-align: center;
        transition: var(--transition);
        margin: var(--spacing-md) 0;
    }}

    .metric-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px var(--shadow);
    }}

    .metric-value {{
        font-size: 2rem;
        font-weight: var(--font-weight-bold);
        color: var(--primary);
        display: block;
        margin-bottom: var(--spacing-sm);
    }}

    .metric-label {{
        font-size: var(--font-size-sm);
        color: var(--text-muted);
        font-weight: var(--font-weight-medium);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}

    /* ENTERPRISE PAGE TITLE */
    .page-title {{
        font-size: 2rem;
        font-weight: var(--font-weight-bold);
        color: var(--text-primary);
        margin: 0 0 var(--spacing-sm) 0;
    }}

    .page-subtitle {{
        font-size: var(--font-size-lg);
        color: var(--text-muted);
        margin: 0 0 var(--spacing-xl) 0;
    }}

    /* HIDE STREAMLIT ELEMENTS */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    .stDeployButton {{visibility: hidden;}}

    /* RESPONSIVE DESIGN */
    @media (max-width: 768px) {{
        .main .block-container {{
            padding: var(--spacing-md);
            margin: var(--spacing-sm);
        }}

        .page-title {{
            font-size: 1.5rem;
        }}
    }}
    </style>
    """

    st.markdown(css, unsafe_allow_html=True)

# --------------------------
# ENTERPRISE CONFIGURATION
# --------------------------
st.set_page_config(
    page_title="FlavorBot Enterprise", 
    page_icon="🍲", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "feedback_submitted" not in st.session_state:
    st.session_state.feedback_submitted = set()

if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"

if "user_preferences" not in st.session_state:
    st.session_state.user_preferences = load_user_preferences()

# Apply enterprise theme
apply_enterprise_styling(st.session_state.user_preferences.get("theme", "light"))

# --------------------------
# ENTERPRISE HEADER
# --------------------------
st.markdown("""
<div class="enterprise-header">
    <div class="header-content">
        <div class="logo-section">
            <div class="company-logo">🍲 FlavorBot Enterprise</div>
            <span style="color: var(--text-muted); font-size: 0.875rem;">AI-Powered Recipe Management Platform</span>
        </div>
        <div class="user-actions">
            <span style="color: var(--text-secondary);">Welcome, Chef</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --------------------------
# ENTERPRISE NAVIGATION
# --------------------------
pages = ["Dashboard", "Recipe Chat", "Recipe Library", "Shopping Lists", "Analytics", "Settings"]
page_icons = ["📊", "💬", "📚", "🛒", "📈", "⚙️"]

# Simple selectbox navigation
selected_page = st.selectbox("Navigate to", 
                           [f"{icon} {page}" for icon, page in zip(page_icons, pages)], 
                           index=[f"{icon} {page}" for icon, page in zip(page_icons, pages)].index(f"{page_icons[pages.index(st.session_state.current_page)]} {st.session_state.current_page}"))

# Extract page name from selection
new_page = selected_page.split(" ", 1)[1] if " " in selected_page else selected_page
if new_page != st.session_state.current_page:
    st.session_state.current_page = new_page
    st.rerun()

# --------------------------
# ENTERPRISE SIDEBAR
# --------------------------
with st.sidebar:
    st.markdown("### 🎯 Quick Actions")

    if st.button("🔄 New Recipe Session", use_container_width=True):
        st.session_state.messages = []
        st.session_state.feedback_submitted = set()
        st.session_state.current_page = "Recipe Chat"
        st.rerun()

    if st.button("📊 View Analytics", use_container_width=True):
        st.session_state.current_page = "Analytics"
        st.rerun()

    st.markdown("### 🔧 Preferences")

    # Theme toggle
    current_theme = st.session_state.user_preferences.get("theme", "light")
    new_theme = st.selectbox("Theme", ["light", "dark"], index=0 if current_theme == "light" else 1)
    if new_theme != current_theme:
        st.session_state.user_preferences["theme"] = new_theme
        save_user_preferences(st.session_state.user_preferences)
        st.rerun()

    # Quick filters
    diet = st.selectbox("Diet", ["", "🌱 Vegan", "🥗 Vegetarian", "🥓 Keto", "🌾 Gluten-free"])
    time = st.selectbox("Prep Time", ["", "⚡ Under 30 min", "⏰ Under 1 hour", "⏳ Over 1 hour"])

    st.markdown("### 📊 Quick Stats")
    bookmarks = load_bookmarks()
    analytics = load_analytics_data()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <span class="metric-value">{len(st.session_state.messages)}</span>
            <div class="metric-label">Messages</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <span class="metric-value">{len(bookmarks)}</span>
            <div class="metric-label">Recipes</div>
        </div>
        """, unsafe_allow_html=True)

# --------------------------
# PAGE ROUTING
# --------------------------

if st.session_state.current_page == "Dashboard":
    st.markdown('<h1 class="page-title">Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Overview of your culinary journey</p>', unsafe_allow_html=True)

    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="enterprise-card">
            <div class="card-header">
                <h3 class="card-title">Total Recipes</h3>
                <span style="font-size: 1.5rem;">📚</span>
            </div>
            <div class="metric-value">{}</div>
            <div class="metric-label">Bookmarked recipes</div>
        </div>
        """.format(len(bookmarks)), unsafe_allow_html=True)

    with col2:
        shopping_items = load_shopping_list()

        st.markdown("""
        <div class="enterprise-card">
            <div class="card-header">
                <h3 class="card-title">Shopping Items</h3>
                <span style="font-size: 1.5rem;">🛒</span>
            </div>
            <div class="metric-value">{}</div>
            <div class="metric-label">Items in lists</div>
        </div>
        """.format(len(shopping_items)), unsafe_allow_html=True)

    with col3:
        # SAFE RATING CALCULATION
        avg_rating = 0
        rated_recipes = []

        # Safe filtering for ratings
        for b in bookmarks:
            if isinstance(b, dict) and b.get('rating', 0) > 0:
                rated_recipes.append(b)

        if rated_recipes:
            avg_rating = sum(b['rating'] for b in rated_recipes) / len(rated_recipes)

        st.markdown("""
        <div class="enterprise-card">
            <div class="card-header">
                <h3 class="card-title">Avg Rating</h3>
                <span style="font-size: 1.5rem;">⭐</span>
            </div>
            <div class="metric-value">{:.1f}</div>
            <div class="metric-label">Recipe satisfaction</div>
        </div>
        """.format(avg_rating), unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="enterprise-card">
            <div class="card-header">
                <h3 class="card-title">Chat Sessions</h3>
                <span style="font-size: 1.5rem;">💬</span>
            </div>
            <div class="metric-value">{}</div>
            <div class="metric-label">Conversations</div>
        </div>
        """.format(len(st.session_state.messages)), unsafe_allow_html=True)

    # Recent Activity
    st.markdown("### 📈 Recent Activity")

    if bookmarks:
        # SAFE RECENT BOOKMARKS FILTERING  
        recent_bookmarks = []
        for b in bookmarks:
            if isinstance(b, dict) and 'timestamp' in b:
                recent_bookmarks.append(b)

        # Sort safely
        recent_bookmarks = sorted(recent_bookmarks, key=lambda x: x.get('timestamp', ''), reverse=True)[:5]

        if recent_bookmarks:
            st.markdown("""
            <div class="enterprise-card">
                <div class="card-header">
                    <h3 class="card-title">Recent Recipes</h3>
                    <span class="card-subtitle">Your latest bookmarked recipes</span>
                </div>
            """, unsafe_allow_html=True)

            for bookmark in recent_bookmarks:
                rating_stars = "⭐" * (bookmark.get('rating', 0)) if bookmark.get('rating', 0) > 0 else "Not rated"
                try:
                    formatted_date = datetime.fromisoformat(bookmark['timestamp']).strftime('%Y-%m-%d %H:%M')
                except:
                    formatted_date = bookmark.get('timestamp', 'Unknown date')

                st.markdown(f"""
                <div style="padding: 12px; border-bottom: 1px solid var(--border);">
                    <div style="font-weight: 500; color: var(--text-primary); margin-bottom: 4px;">{bookmark.get('query', 'Untitled Recipe')}</div>
                    <div style="font-size: 0.875rem; color: var(--text-muted);">
                        {formatted_date} | {rating_stars}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No valid bookmarks found. Start chatting to create your first recipe!")
    else:
        st.info("No recipes bookmarked yet. Start chatting to create your first recipe!")

elif st.session_state.current_page == "Recipe Chat":
    st.markdown('<h1 class="page-title">Recipe Chat</h1>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Get personalized recipe recommendations</p>', unsafe_allow_html=True)

    # Chat interface
    if not st.session_state.messages:
        st.markdown("""
        <div class="enterprise-card">
            <div class="card-header">
                <h3 class="card-title">Welcome to FlavorBot</h3>
                <span class="card-subtitle">Your AI cooking companion</span>
            </div>
            <p>Tell me what ingredients you have, and I'll create personalized recipes for you!</p>
        </div>
        """, unsafe_allow_html=True)

        # Example prompts
        example_prompts = [
            "I have chicken breast, broccoli, and rice",
            "Quick vegetarian dinner for 4 people",
            "Healthy breakfast with oats and berries",
            "Dessert using chocolate and strawberries"
        ]

        col1, col2 = st.columns(2)
        for i, prompt in enumerate(example_prompts):
            with col1 if i % 2 == 0 else col2:
                if st.button(f"💡 {prompt}", key=f"prompt_{i}", use_container_width=True):
                    st.session_state.messages = [{"role": "user", "content": prompt}]
                    st.rerun()

    # Display messages
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

            if (msg["role"] == "assistant" and 
                i > 0 and  
                i not in st.session_state.feedback_submitted):

                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("👍 Helpful", key=f"up_{i}"):
                        st.session_state.feedback_submitted.add(i)
                        st.success("Thank you for your feedback!")
                        st.rerun()

                with col2:
                    if st.button("🔖 Bookmark", key=f"bookmark_{i}"):
                        user_query = st.session_state.messages[i-1]["content"] if i > 0 else "Recipe"
                        if add_bookmark(msg["content"], user_query):
                            st.success("Recipe bookmarked!")
                            st.rerun()

                with col3:
                    if st.button("🛒 Add to Shopping", key=f"shopping_{i}"):
                        ingredients = extract_ingredients_from_recipe(msg["content"])
                        if ingredients and add_to_shopping_list(ingredients):
                            st.success(f"Added {len(ingredients)} items!")
                            update_analytics("shopping_list")
                            st.rerun()

# Chat input - CORRECTED VERSION
if user_input := st.chat_input("What would you like to cook today?"):
    filters = [f for f in [diet, time] if f]
    filter_str = ". ".join(filters)
    full_input = user_input
    if filter_str:
        full_input += f". Please consider: {filter_str}"

    st.session_state.messages.append({"role": "user", "content": user_input})
    update_analytics("recipe_request")

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Creating your recipe..."):
            try:
                # 🔧 CORRECTED: Provide chat_history in the correct format
                chat_history = []
                for msg in st.session_state.messages[-6:]:  # Last 6 messages
                    if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                        chat_history.append(msg)
                
                # Call with both parameters
                response = run_flavorbot(full_input, chat_history)
                
            except Exception as e:
                st.error(f"Error details: {str(e)}")
                response = f"I encountered an error: {str(e)}. Let's try again!"

        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()


elif st.session_state.current_page == "Recipe Library":
    st.markdown('<h1 class="page-title">Recipe Library</h1>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Manage your saved recipes</p>', unsafe_allow_html=True)

    if not bookmarks:
        st.markdown("""
        <div class="enterprise-card">
            <div class="card-header">
                <h3 class="card-title">No Recipes Yet</h3>
            </div>
            <p>Start chatting with FlavorBot to bookmark your first recipe!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Search and filters
        col1, col2 = st.columns([3, 1])
        with col1:
            search_term = st.text_input("🔍 Search recipes...", placeholder="Search by ingredient, cuisine, or name")
        with col2:
            sort_by = st.selectbox("Sort by", ["Newest", "Rating", "Name"])

        # Display recipes - SAFE VERSION
        filtered_bookmarks = bookmarks
        if search_term:
            filtered_bookmarks = [b for b in bookmarks if isinstance(b, dict) and 
                                (search_term.lower() in b.get('query', '').lower() or 
                                 search_term.lower() in b.get('recipe', '').lower())]

        if sort_by == "Rating":
            filtered_bookmarks = sorted(filtered_bookmarks, key=lambda x: x.get('rating', 0) if isinstance(x, dict) else 0, reverse=True)
        elif sort_by == "Name":
            filtered_bookmarks = sorted(filtered_bookmarks, key=lambda x: x.get('query', '') if isinstance(x, dict) else '')
        else:  # Newest
            filtered_bookmarks = sorted(filtered_bookmarks, key=lambda x: x.get('timestamp', '') if isinstance(x, dict) else '', reverse=True)

        for bookmark in filtered_bookmarks:
            if not isinstance(bookmark, dict):
                continue

            st.markdown(f"""
            <div class="enterprise-card">
                <div class="card-header">
                    <div>
                        <h3 class="card-title">{bookmark.get('query', 'Untitled Recipe')}</h3>
                        <p class="card-subtitle">{datetime.fromisoformat(bookmark.get('timestamp', datetime.now().isoformat())).strftime('%B %d, %Y')}</p>
                    </div>
                    <div>
                        {"⭐" * (bookmark.get('rating', 0))}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("View Recipe"):
                st.markdown(bookmark.get('recipe', 'No recipe content'))

                col1, col2, col3 = st.columns(3)
                with col1:
                    # Rating system
                    new_rating = st.selectbox(
                        "Rate", 
                        [0, 1, 2, 3, 4, 5], 
                        index=bookmark.get('rating', 0),
                        key=f"rating_{bookmark.get('id', 0)}"
                    )
                    if new_rating != bookmark.get('rating', 0):
                        rate_bookmark(bookmark.get('id'), new_rating)
                        st.success("Rating updated!")
                        st.rerun()

                with col2:
                    if st.button("🛒 Add to Shopping", key=f"shop_{bookmark.get('id', 0)}"):
                        ingredients = extract_ingredients_from_recipe(bookmark.get('recipe', ''))
                        if add_to_shopping_list(ingredients):
                            st.success(f"Added {len(ingredients)} items!")

                with col3:
                    if st.button("🗑️ Delete", key=f"delete_{bookmark.get('id', 0)}"):
                        if remove_bookmark(bookmark.get('id')):
                            st.success("Recipe deleted!")
                            st.rerun()

elif st.session_state.current_page == "Shopping Lists":
    st.markdown('<h1 class="page-title">Shopping Lists</h1>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Manage your ingredient shopping lists</p>', unsafe_allow_html=True)

    shopping_list = load_shopping_list()

    # Add new item
    col1, col2 = st.columns([3, 1])
    with col1:
        new_item = st.text_input("Add item manually:", placeholder="Enter ingredient...")
    with col2:
        if st.button("➕ Add", key="add_manual"):
            if new_item:
                add_to_shopping_list([new_item])
                st.success("Item added!")
                st.rerun()

    # Clear all button
    if st.button("🗑️ Clear All", key="clear_all"):
        save_shopping_list([])
        st.success("Shopping list cleared!")
        st.rerun()

    if not shopping_list:
        st.info("Your shopping list is empty! Add recipes from the chat or bookmarks.")
    else:
        st.write(f"**{len(shopping_list)}** items in your list:")

        updated_list = []
        for i, item in enumerate(shopping_list):
            col1, col2 = st.columns([4, 1])

            with col1:
                if isinstance(item, dict):
                    checked = st.checkbox(
                        item.get('item', 'Unknown item'), 
                        value=item.get('checked', False),
                        key=f"item_{i}"
                    )
                    item['checked'] = checked
                else:
                    # Handle legacy string items
                    checked = st.checkbox(
                        str(item), 
                        value=False,
                        key=f"item_{i}"
                    )
                    item = {"item": str(item), "checked": checked, "added": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

            with col2:
                if st.button("❌", key=f"remove_{i}", help="Remove item"):
                    continue  # Skip this item (remove it)

            updated_list.append(item)

        # Save updated list
        if updated_list != shopping_list:
            save_shopping_list(updated_list)

elif st.session_state.current_page == "Analytics":
    st.markdown('<h1 class="page-title">Analytics</h1>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Insights into your cooking patterns</p>', unsafe_allow_html=True)

    # Analytics dashboard
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="enterprise-card">
            <div class="card-header">
                <h3 class="card-title">Recipe Trends</h3>
            </div>
            <p>Your cooking activity over time</p>
            <div class="metric-value">{}</div>
            <div class="metric-label">Total requests</div>
        </div>
        """.format(len(analytics.get('daily_interactions', []))), unsafe_allow_html=True)

    with col2:
        bookmark_count = len([b for b in bookmarks if isinstance(b, dict)])
        st.markdown("""
        <div class="enterprise-card">
            <div class="card-header">
                <h3 class="card-title">Recipe Collection</h3>
            </div>
            <p>Your saved recipe library</p>
            <div class="metric-value">{}</div>
            <div class="metric-label">Bookmarked recipes</div>
        </div>
        """.format(bookmark_count), unsafe_allow_html=True)

else:  # Settings
    st.markdown('<h1 class="page-title">Settings</h1>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Customize your FlavorBot experience</p>', unsafe_allow_html=True)

    st.markdown("""
    <div class="enterprise-card">
        <div class="card-header">
            <h3 class="card-title">User Preferences</h3>
        </div>
        <p>Manage your account settings and preferences</p>
    </div>
    """, unsafe_allow_html=True)

    # Settings form
    with st.form("settings_form"):
        st.subheader("Dietary Preferences")
        dietary_restrictions = st.multiselect(
            "Select dietary restrictions:",
            ["Vegetarian", "Vegan", "Gluten-free", "Dairy-free", "Nut-free", "Low-sodium"]
        )

        cooking_skill = st.select_slider(
            "Cooking skill level:",
            options=["Beginner", "Intermediate", "Advanced", "Expert"]
        )

        if st.form_submit_button("Save Settings"):
            prefs = st.session_state.user_preferences
            prefs["dietary_restrictions"] = dietary_restrictions
            prefs["cooking_skill"] = cooking_skill.lower()
            save_user_preferences(prefs)
            st.success("Settings saved successfully!")
