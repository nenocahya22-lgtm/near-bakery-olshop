# Near Bakery & Co — Olshop (HTML/CSS/JS Murni)

## Fitur
- Halaman **Home/Produk** (index.html)
  - Katalog produk dengan gambar ikon, detail harga & rating
  - Search + filter kategori
  - Stepper jumlah + tombol **Masukkan** ke keranjang
- Halaman **Cart** (cart.html)
  - Keranjang memakai `localStorage` key: `near_cart`
  - Update jumlah (+/-), hapus item, kosongkan keranjang
  - Hitung subtotal + admin (1%) + ongkir (gratis jika subtotal ≥ 150rb)
- Halaman **Checkout** (checkout.html)
  - Form nama, WhatsApp, alamat, metode pengiriman, catatan
  - Simulasi konfirmasi pesanan (toast) dan clear keranjang setelah submit

## Cara Menjalankan
1. Buka file langsung di browser:
   - `near-bakery-olshop/index.html`
   - `near-bakery-olshop/cart.html`
   - `near-bakery-olshop/checkout.html`

> Tidak butuh instalasi server. Namun untuk keamanan beberapa browser, localStorage tetap jalan dengan mode file.

