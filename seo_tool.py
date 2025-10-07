import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

st.set_page_config(page_title="Free SEO Tool", layout="wide")
st.title("🧰 Free SEO Analyzer")
st.write("Analyze your website’s On-Page and Technical SEO for free!")

# ---------- Helper Functions ----------
def get_html(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Free-SEO-Tool)"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        return None

def extract_meta(soup):
    title = soup.title.string.strip() if soup.title else ""
    desc = soup.find("meta", attrs={"name": "description"})
    desc = desc["content"] if desc and "content" in desc.attrs else ""
    canonical = soup.find("link", rel="canonical")
    canonical = canonical["href"] if canonical else ""
    return {"title": title, "description": desc, "canonical": canonical}

def get_headings(soup):
    headings = {}
    for tag in ["h1", "h2", "h3"]:
        headings[tag] = [h.get_text(strip=True) for h in soup.find_all(tag)]
    return headings

def get_word_stats(soup):
    text = soup.get_text(separator=" ", strip=True)
    words = re.findall(r"\b\w+\b", text)
    total = len(words)
    top_words = {}
    for w in words:
        w = w.lower()
        top_words[w] = top_words.get(w, 0) + 1
    top = sorted(top_words.items(), key=lambda x: x[1], reverse=True)[:20]
    return total, top

def robots_and_sitemap(url):
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    robots = requests.get(urljoin(base, "/robots.txt")).text[:1000]
    sitemap = requests.get(urljoin(base, "/sitemap.xml")).text[:1000]
    return robots, sitemap

def pagespeed_api(url):
    api = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}"
    try:
        data = requests.get(api).json()
        score = data["lighthouseResult"]["categories"]["performance"]["score"] * 100
        return score
    except:
        return None

# ---------- UI ----------
url = st.text_input("Enter URL", "https://example.com")
if st.button("Analyze SEO"):
    html = get_html(url)
    if not html:
        st.error("Failed to fetch website.")
    else:
        soup = BeautifulSoup(html, "html.parser")

        # On-Page
        st.header("🔍 On-Page SEO")
        meta = extract_meta(soup)
        st.write("**Title:**", meta["title"])
        st.write("**Description:**", meta["description"])
        st.write("**Canonical:**", meta["canonical"])

        headings = get_headings(soup)
        st.write("**Headings:**")
        for tag, vals in headings.items():
            st.write(f"{tag.upper()} ({len(vals)}) → {vals[:5]}")

        total, top = get_word_stats(soup)
        st.write("**Word Count:**", total)
        st.write("**Top Words:**", top)

        # Technical
        st.header("⚙️ Technical SEO")
        robots, sitemap = robots_and_sitemap(url)
        st.write("**robots.txt:**")
        st.code(robots)
        st.write("**sitemap.xml:**")
        st.code(sitemap)

        score = pagespeed_api(url)
        if score:
            st.success(f"PageSpeed Score: {score}/100")
        else:
            st.warning("PageSpeed score unavailable.")

        # Summary
        st.header("✅ Summary Suggestions")
        suggestions = []
        if len(meta["title"]) == 0:
            suggestions.append("Add a title tag.")
        if len(meta["description"]) < 50:
            suggestions.append("Meta description too short.")
        if len(headings["h1"]) == 0:
            suggestions.append("Add at least one H1 heading.")
        if total < 300:
            suggestions.append("Add more content (minimum 300 words).")
        if not meta["canonical"]:
            suggestions.append("Add a canonical tag.")

        if suggestions:
            for s in suggestions:
                st.write("•", s)
        else:
            st.success("Your SEO looks great! 🎉")
