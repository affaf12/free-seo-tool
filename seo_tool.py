import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import time

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
        st.error(f"Failed to fetch website HTML: {e}")
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
    try:
        robots = requests.get(urljoin(base, "/robots.txt"), timeout=10).text[:1000]
    except:
        robots = "robots.txt not available"
    try:
        sitemap = requests.get(urljoin(base, "/sitemap.xml"), timeout=10).text[:1000]
    except:
        sitemap = "sitemap.xml not available"
    return robots, sitemap

def pagespeed_api(url):
    api_key = "AIzaSyDdhpIwUvdcSG8SIwdcA6xBfSgYqIwE_S8"
    api = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&key={api_key}"
    try:
        resp = requests.get(api, timeout=15)
        data = resp.json()
        # Check if API returned lighthouseResult
        if "lighthouseResult" in data and "categories" in data["lighthouseResult"]:
            score = data["lighthouseResult"]["categories"]["performance"]["score"] * 100
            return score
        else:
            st.warning(f"PageSpeed API could not process this URL. API Response: {data.get('error', data)}")
            return None
    except Exception as e:
        st.warning(f"PageSpeed API error: {e}")
        return None

def simple_speed_test(url):
    start = time.time()
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return round(time.time() - start, 2)
    except Exception as e:
        st.warning(f"Fallback speed test failed: {e}")
        return None

# ---------- UI ----------
url = st.text_input("Enter URL", "https://example.com")

if st.button("Analyze SEO"):
    html = get_html(url)
    if not html:
        st.error("Failed to fetch website.")
    else:
        soup = BeautifulSoup(html, "html.parser")

        # On-Page SEO
        st.header("🔍 On-Page SEO")
        meta = extract_meta(soup)
        st.write("**Title:**", meta["title"])
        st.write("**Description:**", meta["description"])
        st.write("**Canonical:**", meta["canonical"] or "No canonical tag found")

        headings = get_headings(soup)
        st.write("**Headings:**")
        for tag, vals in headings.items():
            st.write(f"{tag.upper()} ({len(vals)}) → {vals[:5]}")

        total, top = get_word_stats(soup)
        st.write("**Word Count:**", total)
        st.write("**Top Words:**", top)

        # Technical SEO
        st.header("⚙️ Technical SEO")
        robots, sitemap = robots_and_sitemap(url)
        st.write("**robots.txt:**")
        st.code(robots)
        st.write("**sitemap.xml:**")
        st.code(sitemap)

        # Page Speed
        score = pagespeed_api(url)
        if score:
            st.success(f"PageSpeed Score: {score}/100")
        else:
            st.info("PageSpeed API unavailable. Running fallback speed test...")
            speed = simple_speed_test(url)
            if speed:
                st.info(f"⏱️ Page loaded in {speed} seconds (fallback test)")
            else:
                st.error("⚠️ Could not measure page speed.")

        # Summary Suggestions
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
