import streamlit as st
import pandas as pd
import json
import os
import time

from database_engine import get_connection
from order_notifications import wa_link, order_to_message

# Use format_rp if available; fallback to simple IDR formatting.
try:
    from utils import format_rp
except Exception:
    def format_rp(value):
        try:
            return f"Rp {float(value):,.0f}".replace(",", ".")
        except:
            return f"Rp {value}"


# NOTE:
# This is an OLShop-only Streamlit app.
# It provides: Home/Katalog, Cart (session_state), Checkout (writes to DB).

st.set_page_config(page_title="Near Bakery & Co. (Olshop)", page_icon="🥐", layout="wide")

# --- Session State ---
if "cart" not in st.session_state:
    st.session_state.cart = {}
if "page" not in st.session_state:
    st.session_state.page = "SHOP"

# --- UI CSS ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Montserrat:wght@300;400;500;600;700&display=swap');
    html, body, [class*="st-"] {
        font-family: 'Montserrat', sans-serif !important;
        background: #FAFAF8 !important;
        color: #2C2C2C;
    }

    .ob-header {
        position: sticky; top: 0; z-index: 10;
        background: rgba(255,255,255,0.9);
        backdrop-filter: blur(12px);
        border-bottom: 1px solid rgba(0,0,0,0.06);
        padding: 14px 18px;
        display: flex; align-items: center; justify-content: space-between;
    }
    .ob-brand {
        font-family: 'Playfair Display', serif;
        font-weight: 800;
        letter-spacing: -0.5px;
        font-size: 1.3rem;
    }
    .ob-btn {
        border: 1px solid rgba(0,0,0,0.08);
        background: white;
        border-radius: 12px;
        padding: 10px 14px;
        font-weight: 800;
        cursor: pointer;
    }

    .page-wrap { padding: 20px 10% 40px; }

    .catalog-container { padding-top: 18px; }

    .nb-card {
        background: white;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(0,0,0,0.06);
        margin-bottom: 18px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.02);
        transition: 0.2s;
    }
    .nb-card:hover { transform: translateY(-2px); box-shadow: 0 12px 30px rgba(0,0,0,0.06); }

    .plus-btn div[data-testid="stButton"] button {
        background: #1A1A1A !important;
        color: white !important;
        width: 40px !important;
        height: 40px !important;
        min-width: 40px !important;
        border-radius: 50% !important;
        border: none !important;
        font-size: 1.1rem !important;
        padding: 0 !important;
    }

    .ob-title { font-family: 'Playfair Display', serif; font-size: 2.4rem; font-weight: 800; margin: 0 0 12px; }

    .ob-footer {
        background: #F9F9F9;
        padding: 32px 10%;
        border-top: 1px solid #EEE;
        margin-top: 30px;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Helpers ---
def load_products():
    conn = get_connection()
    try:
        products = pd.read_sql_query("SELECT * FROM recipe_master ORDER BY name ASC", conn)
        return products
    finally:
        conn.close()


def render_header():
    total_qty = sum(it.get("qty", 0) for it in st.session_state.cart.values())
    st.markdown(
        """
        <div class='ob-header'>
            <div class='ob-brand'>Near Bakery & Co.</div>
            <div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("🏠", key="ob_home", help="Home"):
            st.session_state.page = "SHOP"
            st.rerun()
    with c2:
        cart_lbl = f"🛒 {total_qty}" if total_qty > 0 else "🛒"
        if st.button(cart_lbl, key="ob_cart", help="Keranjang"):
            if total_qty > 0:
                st.session_state.page = "CART"
            else:
                st.toast("Keranjang masih kosong 🥐")
            st.rerun()
    st.markdown("</div></div>", unsafe_allow_html=True)


def show_shop_page():
    products = load_products()

    st.markdown("<div class='page-wrap'>", unsafe_allow_html=True)

    # Hero (simple)
    st.markdown(
        """
        <div style="width:100%; height:280px; border-radius:18px; overflow:hidden; background:url('https://images.unsplash.com/photo-1509440159596-0249088772ff?q=80&w=1500&auto=format&fit=crop') center/cover; display:flex; align-items:center; justify-content:center;">
            <div style="text-align:center; background:rgba(0,0,0,0.35); padding:20px 28px; border-radius:16px; color:white;">
                <div style="font-family: 'Playfair Display', serif; font-size:40px; font-weight:800; letter-spacing:-0.5px;">Near Bakery & Co.</div>
                <div style="margin-top:6px; font-weight:800; letter-spacing:4px; text-transform:uppercase; font-size:12px; opacity:0.9;">Baked Fresh Daily in Surabaya</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='catalog-container'>", unsafe_allow_html=True)
    st.markdown("<h2 style='font-family:Playfair Display; text-align:center; margin:26px 0 6px;'>Katalog Menu</h2>", unsafe_allow_html=True)

    if products.empty:
        st.warning("Belum ada produk di recipe_master.")
        st.markdown("</div></div>", unsafe_allow_html=True)
        return

    # Categories
    if "category" in products.columns:
        cats = ["Semua"] + sorted(products["category"].fillna("LAINNYA").unique().tolist())
    else:
        cats = ["Semua"]

    tabs = st.tabs(cats)

    for i, tab in enumerate(tabs):
        with tab:
            df = products if i == 0 else products[products.get("category").fillna("LAINNYA") == cats[i]]
            cols = st.columns(3)
            for idx, row in df.iterrows():
                with cols[idx % 3]:
                    with st.container():
                        st.markdown('<div class="nb-card">', unsafe_allow_html=True)

                        img_path = row.get("image_path")
                        if isinstance(img_path, str) and os.path.exists(img_path):
                            img_src = img_path
                        else:
                            img_src = "https://images.unsplash.com/photo-1555507036-ab1f4038808a?q=80&w=1000&auto=format&fit=crop"

                        st.markdown(
                            f"""
                            <div style='width:100%; height:190px; overflow:hidden;'>
                                <img src='{img_src}' style='width:100%; height:100%; object-fit:cover;'>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        st.markdown(
                            f"""
                            <div style='padding:12px 14px; text-align:center;'>
                                <div style='font-size:0.65rem; color:#C9A96E; font-weight:800; letter-spacing:2px; margin-bottom:6px; text-transform:uppercase;'>
                                    {(str(row.get('category','LAINNYA'))).upper()}
                                </div>
                                <div style='font-family:Playfair Display; font-size:1.2rem; font-weight:800; line-height:1.15;'>
                                    {str(row.get('name','')).title()}
                                </div>
                                <div style='color:#888; font-size:0.95rem; margin-top:6px; font-weight:900;'>{format_rp(row.get('selling_price',0))}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        st.markdown('<div class="plus-btn">', unsafe_allow_html=True)
                        if st.button("+", key=f"ol_add_{row['id']}"):
                            pid = str(row["id"])
                            if pid in st.session_state.cart:
                                st.session_state.cart[pid]["qty"] += 1
                            else:
                                st.session_state.cart[pid] = {
                                    "name": row.get("name"),
                                    "price": float(row.get("selling_price", 0) or 0),
                                    "qty": 1,
                                    "img": img_src,
                                }
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)

                        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    show_footer()
    st.markdown("</div>", unsafe_allow_html=True)


def show_cart_page():
    st.markdown("<div class='page-wrap'>", unsafe_allow_html=True)
    st.markdown("<div class='ob-title'>Keranjang Saya</div>", unsafe_allow_html=True)

    if not st.session_state.cart:
        st.info("Keranjang kosong.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    total = 0
    for pid, it in list(st.session_state.cart.items()):
        c1, c2, c3 = st.columns([1, 4, 1])
        if it.get("img"):
            c1.image(it["img"], width=70)
        else:
            c1.markdown("🥐")

        c2.markdown(f"**{it['name']}**  \n{it['qty']} x {format_rp(it['price'])}")

        if c3.button("🗑️", key=f"ol_del_{pid}"):
            del st.session_state.cart[pid]
            st.rerun()

        total += float(it["qty"]) * float(it["price"])

    st.divider()
    st.markdown(f"### Total: {format_rp(total)}")

    if st.button("LANJUT KE PENGIRIMAN", type="primary", use_container_width=True):
        st.session_state.page = "CHECKOUT"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def show_checkout_page():
    st.markdown("<div class='page-wrap'>", unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom:10px;'><h2 style='font-family:Playfair Display; margin:0;'>Pengiriman</h2></div>", unsafe_allow_html=True)

    if st.button("← Kembali ke Keranjang", key="ol_bk_cart"):
        st.session_state.page = "CART"
        st.rerun()

    with st.form("ol_checkout_form"):
        c_name = st.text_input("Nama")
        c_wa = st.text_input("WhatsApp")
        c_addr = st.text_area("Alamat")

        if st.form_submit_button("KONFIRMASI PESANAN"):
            if not (c_name and c_wa and c_addr):
                st.warning("Lengkapi data pengiriman.")
                st.stop()

            total_amt = sum(float(it["qty"]) * float(it["price"]) for it in st.session_state.cart.values())

            conn = get_connection()
            try:
                # Insert order
                res = conn.execute(
                    "INSERT INTO online_orders (customer_name, whatsapp, customer_address, items_json, total_amount) VALUES (?,?,?,?,?) RETURNING id",
                    (c_name, c_wa, c_addr, json.dumps(list(st.session_state.cart.values())), total_amt),
                )
                order_id_row = res.fetchone() if hasattr(res, "fetchone") else None
                order_id = order_id_row[0] if order_id_row else None

                # Insert notification
                try:
                    conn.execute(
                        """
                        CREATE TABLE IF NOT EXISTS online_order_notifications (
                            id SERIAL PRIMARY KEY,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            order_id INTEGER,
                            message TEXT,
                            wa_link TEXT,
                            status TEXT DEFAULT 'NEW'
                        )
                        """
                    )
                    conn.commit()
                except:
                    pass

                if order_id:
                    admin_phone = "083833622282"
                    msg = order_to_message(int(order_id), c_name, float(total_amt))
                    link = wa_link(admin_phone, msg)

                    try:
                        conn.execute(
                            "INSERT INTO online_order_notifications (order_id, message, wa_link, status) VALUES (?,?,?,?)",
                            (int(order_id), msg, link, "NEW"),
                        )
                        conn.commit()
                    except:
                        # non-blocking
                        pass
            finally:
                conn.close()

            st.success("Berhasil! Pesanan masuk.")
            st.session_state.cart = {}
            st.session_state.page = "SHOP"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def show_footer():
    st.markdown(
        """
        <div class='ob-footer'>
            <h4 style='font-family:Playfair Display; margin:0;'>Near Bakery & Co.</h4>
            <p style='color:#999; font-size:0.7rem; margin-top:6px;'>Surabaya</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --- Render ---
render_header()

if st.session_state.page == "CART":
    show_cart_page()
elif st.session_state.page == "CHECKOUT":
    show_checkout_page()
else:
    show_shop_page()

