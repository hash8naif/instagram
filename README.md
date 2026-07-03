# Hash – Instagram Profile Viewer (v2.0) 🚀

A sleek, desktop-based OSINT and data extraction GUI utility engineered to fetch comprehensive public data from Instagram profiles efficiently using session cookies. 

Developed by **naif · khaled**.

---

## 📖 Features

* 🎨 **Modern Dark UI/UX:** Styled using a custom dark theme (`DARK_STYLE`) with responsive layouts for a smooth visual experience.
* 🧵 **Asynchronous Multi-Threading:** Implements `QThread` (`FetchWorker`) to handle network requests in the background, keeping the main interface highly responsive and preventing UI freezing.
* 🛡️ **Robust Anti-Rate Limiting:** Automatically detects `HTTP 429` (Too Many Requests) errors and utilizes smart retry logic (up to 3 attempts) to bypass temporary blocks.
* 📥 **Automated Cookie Parser:** Features a JSON loading mechanism to map authentication parameters (`sessionid`, `csrftoken`, `ds_user_id`) instantaneously[cite: 1].

---

## 📊 Extracted Data Points

The application performs a deep inspect on the target account, extracting and formatting the following metrics into `hash_gui.py`[cite: 1]:

* **Identity & Core Metadata:** Full name, User ID, account privacy status (Public/Private), and verification badges[cite: 1].
* **Business & Professional Insights:** Business categories, public contact emails, phone numbers, and full geographic addresses (Street, City, Zip code)[cite: 1].
* **Real-time Statistics:** Exact counts for Followers, Following, Posts, Reels, IGTV videos, and Highlights[cite: 1].
* **Biography Analysis:** Biography text, external URLs, bio links, and the direct URL to the high-resolution profile picture[cite: 1].
* **Relationship Status:** Instantly tracks mutual relationships (whether you follow them or they follow you)[cite: 1].

---

## 🚀 Installation & Usage

### Prerequisites
Make sure you have Python 3.x installed on your system.

### 1. Clone the repository
```bash
git clone [https://github.com/yourusername/hash-instagram-viewer.git](https://github.com/yourusername/hash-instagram-viewer.git)
cd hash-instagram-viewer
