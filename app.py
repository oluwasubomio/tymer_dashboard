import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px
from datetime import datetime, timedelta

# Page config
st.set_page_config(
    page_title="Tymer Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# Supabase connection
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Custom CSS
st.markdown("""
<style>
.metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 20px;
    border-radius: 15px;
    color: white;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}
.big-number {
    font-size: 48px;
    font-weight: bold;
    margin: 10px 0;
}
.metric-label {
    font-size: 14px;
    opacity: 0.9;
}
</style>
""", unsafe_allow_html=True)

# Data fetching functions
@st.cache_data(ttl=60)
def load_contact_messages():
    try:
        response = supabase.table("contact_messages").select("*").execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            time_cols = [col for col in df.columns if 'created' in col.lower() or 'time' in col.lower()]
            if time_cols:
                df[time_cols[0]] = pd.to_datetime(df[time_cols[0]], utc=True)
                df = df.rename(columns={time_cols[0]: 'request_time'})
        return df
    except Exception as e:
        st.error(f"Error loading contact messages: {e}")
        return pd.DataFrame()

# Load data
contact_df = load_contact_messages()

# Header
st.title("📊 Tymer.me Analytics Dashboard")
st.markdown("**Real-time insights from your contact forms**")
st.markdown("---")

# KPI Section
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-label">📨 TOTAL MESSAGES</div>
        <div class="big-number">{}</div>
    </div>
    """.format(len(contact_df)), unsafe_allow_html=True)

with col2:
    today_messages = 0
    if not contact_df.empty and 'request_time' in contact_df.columns:
        today = pd.Timestamp.now(tz='UTC').normalize()
        today_messages = len(contact_df[contact_df['request_time'].dt.normalize() == today])
    
    st.markdown("""
    <div class="metric-card">
        <div class="metric-label">📅 TODAY</div>
        <div class="big-number">{}</div>
    </div>
    """.format(today_messages), unsafe_allow_html=True)

with col3:
    last_7_days = 0
    if not contact_df.empty and 'request_time' in contact_df.columns:
        week_ago = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=7)
        last_7_days = len(contact_df[contact_df['request_time'] >= week_ago])
    
    st.markdown("""
    <div class="metric-card">
        <div class="metric-label">📈 LAST 7 DAYS</div>
        <div class="big-number">{}</div>
    </div>
    """.format(last_7_days), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Charts Section
st.subheader("📈 Submission Trends")

st.markdown("**Contact Messages Over Time**")
if not contact_df.empty and 'request_time' in contact_df.columns:
    daily_contacts = contact_df.groupby(contact_df['request_time'].dt.date).size().reset_index()
    daily_contacts.columns = ['Date', 'Messages']
    
    fig = px.line(daily_contacts, x='Date', y='Messages', 
                 markers=True,
                 line_shape='spline')
    fig.update_traces(line_color='#667eea', marker=dict(size=8))
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No contact message data available")

st.markdown("---")

# Recent Activity Section with Click-to-View
st.subheader("🔔 Recent Activity")

st.markdown("**Latest Contact Messages**")
if not contact_df.empty:
    recent_contacts = contact_df.copy()
    if 'request_time' in recent_contacts.columns:
        recent_contacts = recent_contacts.sort_values('request_time', ascending=False)
    
    # Show preview with name/email only
    preview_cols = []
    for col in ['name', 'email', 'request_time']:
        if col in recent_contacts.columns:
            preview_cols.append(col)
    
    if preview_cols:
        preview_df = recent_contacts[preview_cols].head(10)
        
        # Display as clickable rows
        for idx, row in preview_df.iterrows():
            with st.expander(f"📨 {row.get('name', 'Unknown')} - {row.get('email', '')}"):
                full_row = contact_df[contact_df.index == idx].iloc[0]
                for col, value in full_row.items():
                    if col != 'id':
                        st.write(f"**{col.replace('_', ' ').title()}:** {value}")
    else:
        st.dataframe(recent_contacts.head(10), use_container_width=True, hide_index=True)
else:
    st.info("No messages yet")

st.markdown("---")

# Full Data Table
st.subheader("📋 All Contact Messages")

if not contact_df.empty:
    if 'request_time' in contact_df.columns:
        display_df = contact_df.sort_values('request_time', ascending=False)
    else:
        display_df = contact_df
    
    st.dataframe(display_df, use_container_width=True, height=400)
    
    # Download button
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="📥 Download as CSV",
        data=csv,
        file_name="contact_messages.csv",
        mime="text/csv"
    )
else:
    st.info("No contact messages yet")

# Footer
st.markdown("---")
st.caption("🔄 Data refreshes every 60 seconds | Built with Streamlit & Supabase")