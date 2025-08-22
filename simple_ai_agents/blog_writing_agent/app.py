"""
Newsletter/Blog Writing Agent Streamlit App

A Streamlit application featuring two AI agents:
1. Knowledge Agent: Analyzes uploaded documents to extract writing style, tone, and structure
2. Writing Agent: Generates new content using the stored writing style information

This file contains the Streamlit interface while the agent logic is in agents.py
"""

import streamlit as st
import base64
from agents import (
    initialize_memori,
    create_memory_tool_instance,
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_txt,
    analyze_writing_style,
    store_writing_style_in_memori,
    generate_blog_with_style,
    get_stored_writing_style,
    save_generated_blog,
)

# Page configuration
st.set_page_config(
    page_title="AI Blog Agent",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "query_history" not in st.session_state:
    st.session_state.query_history = []

# Load and encode images
with open("./assets/digital_ocean.png", "rb") as digital_ocean_file:
    digital_ocean_base64 = base64.b64encode(digital_ocean_file.read()).decode()

with open("./assets/gibson.svg", "r", encoding="utf-8") as gibson_file:
    gibson_svg = (
        gibson_file.read()
        .replace("\n", "")
        .replace("\r", "")
        .replace("  ", "")
        .replace('"', "'")
    )

gibson_svg_inline = f'<span style="height:80px; width:200px; display:inline-block; vertical-align:middle; margin-left:8px;margin-top:20px;margin-right:8px;">{gibson_svg}</span>'

# Create title with embedded images (SVG and PNG in one line)
title_html = f"""
<div style='display:flex; align-items:center; width:100%; padding:24px 0;'>
  <h1 style='margin:0; padding:0; font-size:2.5rem; font-weight:bold; display:flex; align-items:center;'>
    <span style='font-size:3rem;'>✍️ </span>Blog Writing Agent with {gibson_svg_inline} &
    <img src='data:image/png;base64,{digital_ocean_base64}' style='height:40px; margin-left:8px; margin-right:8px; vertical-align:middle;'/>
  </h1>
</div>
"""


# Initialize Memori
@st.cache_resource
def get_memory_system():
    """Initialize Memori memory system"""
    try:
        memory_system = initialize_memori()
        return memory_system
    except Exception as e:
        st.error(f"Failed to initialize Memori: {e}")
        return None


# Initialize memory system
memory_system = get_memory_system()
if memory_system is None:
    st.stop()

# Create memory tool
memory_tool = create_memory_tool_instance(memory_system)


def knowledge_agent_sidebar():
    """Knowledge Agent interface in the sidebar"""
    st.sidebar.header("📚 Knowledge Agent")
    st.sidebar.markdown("**Upload & analyze your writing style**")

    # File upload
    uploaded_file = st.sidebar.file_uploader(
        "Upload your article (PDF, DOCX, or TXT)",
        type=["pdf", "docx", "txt"],
        help="Upload a document that represents your writing style",
    )

    if uploaded_file is not None:
        st.sidebar.success(f"✅ File uploaded: {uploaded_file.name}")

        # Extract text based on file type
        text_content = ""
        try:
            if uploaded_file.type == "application/pdf":
                text_content = extract_text_from_pdf(uploaded_file)
            elif (
                uploaded_file.type
                == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ):
                text_content = extract_text_from_docx(uploaded_file)
            elif uploaded_file.type == "text/plain":
                text_content = extract_text_from_txt(uploaded_file)
        except Exception as e:
            st.sidebar.error(f"Error extracting text: {e}")
            return

        if text_content:
            # Text preview in sidebar
            st.sidebar.subheader("📖 Text Preview")
            st.sidebar.text_area(
                "Content",
                (
                    text_content[:500] + "..."
                    if len(text_content) > 500
                    else text_content
                ),
                height=150,
                disabled=True,
            )

            # Analyze button
            if st.sidebar.button("🔍 Analyze Writing Style", type="primary"):
                with st.spinner("Analyzing..."):
                    try:
                        style_analysis = analyze_writing_style(text_content)

                        if style_analysis:
                            st.sidebar.subheader("🎯 Style Analysis")

                            # Display key results compactly
                            st.sidebar.markdown(
                                f"**Tone:** {style_analysis.get('tone', 'N/A')}"
                            )
                            st.sidebar.markdown(
                                f"**Voice:** {style_analysis.get('voice', 'N/A')}"
                            )
                            st.sidebar.markdown(
                                f"**Structure:** {style_analysis.get('structure', 'N/A')[:50]}..."
                            )

                            # Store the analysis results in session state
                            st.session_state.style_analysis = style_analysis
                            st.session_state.text_content = text_content

                            # Automatically store the style in memory
                            with st.spinner("Storing style in memory..."):
                                try:
                                    formatted_style = store_writing_style_in_memori(
                                        memory_system,
                                        st.session_state.style_analysis,
                                        st.session_state.text_content,
                                    )
                                    if formatted_style:
                                        st.sidebar.success(
                                            "✅ Analysis complete & style stored in memory!"
                                        )
                                        st.rerun()  # Refresh to show updated state
                                    else:
                                        st.sidebar.error("❌ Failed to store style")
                                except Exception as e:
                                    st.sidebar.error(f"❌ Error storing style: {e}")
                        else:
                            st.sidebar.error("❌ Failed to analyze style")
                    except Exception as e:
                        st.sidebar.error(f"❌ Error: {e}")

    # Show current style status
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Current Status")

    try:
        stored_style = get_stored_writing_style(memory_tool)
        if stored_style:
            st.sidebar.success("✅ Writing style profile found")
            st.sidebar.info("You can now generate content using the Writing Agent!")
        else:
            st.sidebar.warning("⚠️ No writing style profile")
            st.sidebar.info("Upload a document to get started")
    except Exception as e:
        st.sidebar.error(f"Error: {e}")


def writing_agent_main():
    """Writing Agent interface in the main area"""
    # Display custom HTML title with embedded logos
    st.markdown(title_html, unsafe_allow_html=True)

    st.markdown("**Generate new blog posts using your stored writing style**")

    # Check if we have stored writing style
    try:
        stored_style = get_stored_writing_style(memory_tool)

        if stored_style:
            # st.success("✅ Found your stored writing style profile!")

            # Blog generation
            # st.subheader("📝 Generate New Blog Post")

            # Topic input using chat_input for cleaner interface
            topic = st.chat_input(
                "What topic would you like me to write about? (e.g., The benefits of artificial intelligence in healthcare)"
            )

            if topic:
                with st.spinner(
                    "Still editing your blog post using your unique writing style..."
                ):
                    try:
                        # Generate content using stored style
                        blog_content = generate_blog_with_style(memory_tool, topic)

                        if blog_content:
                            # st.subheader("📝 Generated Blog Post")

                            # Display the blog content
                            st.markdown(blog_content)

                            # Action buttons
                            col1, col2, col3 = st.columns([1, 1, 2])

                            with col1:
                                # Download as text
                                st.download_button(
                                    label="📄 Download TXT",
                                    data=blog_content,
                                    file_name=f"blog_post_{topic.replace(' ', '_')[:30]}.txt",
                                    mime="text/plain",
                                    use_container_width=True,
                                )

                            with col2:
                                # Copy to clipboard
                                if st.button(
                                    "📋 Copy to Clipboard", use_container_width=True
                                ):
                                    st.write("Content copied to clipboard!")

                            with col3:
                                # Store the generated content
                                try:
                                    save_generated_blog(
                                        memory_system, topic, blog_content
                                    )
                                    st.success("💾 Blog post saved to memory!")
                                except Exception as e:
                                    st.warning(f"Note: Could not save to memory: {e}")
                        else:
                            st.error("❌ Failed to generate blog post")
                    except Exception as e:
                        st.error(f"❌ Error generating blog: {e}")

        else:
            st.warning("⚠️ No writing style profile found in memory")
            st.info(
                "Please use the Knowledge Agent in the sidebar to upload and analyze your writing style first."
            )

            # # Show what to do next
            # st.markdown(
            #     """
            #     **Next Steps:**
            #     1. **📚 Use the Knowledge Agent** (in the sidebar)
            #     2. **📄 Upload one of your previous articles**
            #     3. **🔍 Let the agent analyze your writing style**
            #     4. **💾 Store your style profile in memory**
            #     5. **✍️ Come back here to generate new content!**
            #     """
            # )

    except Exception as e:
        st.error(f"Error accessing memory: {e}")
        st.info(
            "Please use the Knowledge Agent in the sidebar to store your writing style profile."
        )


def main():
    # Knowledge Agent in sidebar
    knowledge_agent_sidebar()

    # Writing Agent in main area
    writing_agent_main()


if __name__ == "__main__":
    main()
