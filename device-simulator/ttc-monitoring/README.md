# PDU Monitor (Go MIPS)

Aplikasi ringan berbasis **Go (Golang)** yang dirancang khusus untuk berjalan di *router* industri dengan arsitektur **MIPS** (seperti Teltonika RUT956) melalui sistem operasi OpenWrt/RutOS. Aplikasi ini memantau data kelistrikan PDU (*Power Distribution Unit*) via SNMP dan meneruskannya ke peladen MQTT.

## Fitur Utama
1. **Auto-Discovery via ARP:** Program secara dinamis mencari IP PDU yang tersambung ke antarmuka (*interface*) jaringan spesifik (`eth0.1` untuk PDU-1 dan `eth0.2` untuk PDU-2) dengan membaca tabel ARP lokal secara mandiri.
2. **Payload Statis & Terstruktur:** Data telemetri dikemas dalam JSON dengan urutan yang sudah dikunci (kustom `Struct`), menempatkan `ts` (Unix Millisecond Timestamp) di urutan pertama.
3. **Optimasi Memori:** Program menunda eksekusi selama 10 detik di awal untuk memberi waktu pada OS (*booting*), lalu berjalan ringan di latar belakang (*background*) setiap 60 detik.
4. **Dynamic Topic Injection:** Penamaan topik MQTT (`locationTopicBase`) dapat disuntikkan secara dinamis pada saat kompilasi (Build Time).

## Kebutuhan Sistem (Kompilasi)
- **Go 1.18+** terinstal di Windows/Linux.
- Dukungan *Cross-compilation* untuk OS `linux` dan arsitektur `mipsle`.

## Cara Kompilasi (Build)
Karena program ini butuh disuntikkan nama Topik MQTT yang berbeda untuk setiap wilayah (TTC), Anda wajib mendefinisikan flag `-ldflags "-X main.locationTopicBase=..."` saat melakukan *build*.

### Kompilasi Satu Lokasi (Contoh: Aceh Lembaro)
Jalankan perintah ini di terminal (PowerShell):
```powershell
$env:GOOS="linux"; $env:GOARCH="mipsle"; $env:GOMIPS="softfloat"; go build -trimpath -ldflags "-s -w -X 'main.locationTopicBase=TTC/ACEH-LEMBARO/RACK-01'" -o pdu_monitor_aceh main.go
```

### Kompilasi Banyak Lokasi Sekaligus (Batch Build)
Gunakan susunan perintah PowerShell di bawah ini untuk menghasilkan banyak biner secara otomatis:
```powershell
$env:GOOS="linux"; $env:GOARCH="mipsle"; $env:GOMIPS="softfloat";
$locs = @(
    "TTC/ACEH-LEMBARO/RACK-01",
    "TTC/MEDAN-AMIR-HAMZAH/RACK-01",
    "TTC/BUARAN/RACK-01"
)
foreach ($l in $locs) {
    $name = $l.Split('/')[1].ToLower().Replace('-', '_')
    go build -trimpath -ldflags "-s -w -X main.locationTopicBase=$l" -o "pdu_monitor_$name" main.go
}
```

> **Catatan:** Flag `-trimpath` dan `-ldflags "-s -w"` sangat diwajibkan untuk menekan ukuran file biner sekecil mungkin agar memori flash *router* tidak penuh.

## Cara Pemasangan di Router
1. Transfer file biner yang telah dihasilkan ke router Anda (biasanya diletakkan di `/root/pdu_monitor`).
2. Masuk ke terminal router (SSH) lalu set izin eksekusi:
   ```bash
   chmod +x /root/pdu_monitor
   ```
3. Tambahkan ke *startup* dengan mengedit `/etc/rc.local` (sebelum baris `exit 0`):
   ```bash
   /root/pdu_monitor &
   ```
4. Restart router, dan PDU Monitor akan berjalan secara otomatis di latar belakang.
