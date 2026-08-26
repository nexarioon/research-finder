from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from research_finder.config.settings import get_settings
from research_finder.domain.models import AIAnalysisResult
from research_finder.providers.ai_base import AIProvider

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT_ID = """Anda adalah seorang Analis Sistem Informasi dan Dosen Pembimbing Skripsi di Indonesia yang bertugas membantu mahasiswa menemukan topik riset/skripsi yang relevan dan bernilai guna tinggi bagi bisnis lokal.

Analisis bisnis berikut dan berikan wawasan dalam BAHASA INDONESIA yang baku, profesional, dan realistis:

Nama Bisnis: {name}
Kategori: {category}
Alamat: {address}
Telepon/Kontak: {phone}
Website: {website}
Rating: {rating}
Jumlah Ulasan: {review_count}

{website_analysis}

Berikan analisis Anda dalam format JSON PERSIS seperti berikut (semua teks wajib dalam Bahasa Indonesia):
{{
    "operational_problems": "Deskripsikan 2-3 potensi masalah operasional yang kemungkinan dihadapi bisnis ini berdasarkan jenis usaha dan info publik. Tandai asumsi dengan [ASUMSI].",
    "info_system_opportunities": "Deskripsikan 2-3 peluang solusi digital/sistem informasi yang dapat membantu bisnis ini (misal: sistem inventory, POS, tracking order, CRM, booking web).",
    "research_relevance": "Jelaskan mengapa bisnis ini sangat layak menjadi objek studi kasus penelitian/skripsi mahasiswa.",
    "research_topics": [
        "Judul Skripsi 1 (Format: Pengembangan/Rancang Bangun/Evaluasi Sistem Informasi ... Berbasis ... pada NamaBisnis)",
        "Judul Skripsi 2",
        "Judul Skripsi 3",
        "Judul Skripsi 4",
        "Judul Skripsi 5"
    ],
    "validation_questions": [
        "Pertanyaan wawancara 1 untuk pemilik bisnis",
        "Pertanyaan wawancara 2",
        "Pertanyaan wawancara 3",
        "Pertanyaan wawancara 4"
    ]
}}

Aturan Penting:
- Output WAJIB 100% dalam BAHASA INDONESIA.
- Jangan mengarang data yang tidak masuk akal.
- Fokus pada solusi Sistem Informasi, Rekayasa Perangkat Lunak, atau Transformasi Digital.
- Berikan tepat 3-5 judul topik skripsi yang spesifik dan berbobot akademis.
- Berikan 4-5 pertanyaan validasi untuk wawancara."""


OUTREACH_PROMPT = """Anda adalah asisten permohonan riset skripsi mahasiswa di Indonesia.
Tugas Anda adalah menyusun pesan permohonan wawancara/riset awal yang SANTUN, RENDAH HATI, NATURAL, dan TIDAK MENGASUMSIKAN KENDALA, berpatokan pada MASTER OF TRUTH berikut.

--- MASTER OF TRUTH TEMPLATE ---
Pesan harus mengikuti struktur dan nada berikut:
1. Salam & Perkenalan: "Selamat pagi/siang/sore Bapak/Ibu, perkenalkan saya {student_name}, mahasiswa {major}{university_phrase}."
2. Latar Belakang Penemuan: "Saya menemukan {name} melalui Google Maps/OpenStreetMap dan melihat informasi mengenai layanan serta kontak pemesanan yang tersedia. Saat ini saya sedang melakukan riset awal untuk mencari dan memahami permasalahan nyata yang dihadapi oleh bisnis sebagai persiapan penelitian skripsi."
3. Pertanyaan Eksploratif (TIDAK MENGASUMSIKAN): "Jika Bapak/Ibu tidak keberatan, saya ingin bertanya apakah dalam operasional {name} terdapat proses atau kegiatan yang saat ini masih menjadi kendala, cukup memakan waktu, sering dilakukan secara manual, atau menurut Bapak/Ibu masih dapat dibuat lebih efektif."
4. Personalisasi Kendala Relevan (Lingkup ERP, CRM, SCM, SPK/DSS, BPMN/MPB, SIM Digitalisasi): Sebutkan 2-3 contoh proses spesifik yang sesuai dengan jenis usaha {category} (misal: pengelolaan jadwal & booking lapangan, pencatatan pembayaran, manajemen persediaan/stok, layanan pelanggan, koordinasi operasional). Lalu tambahkan: "Namun, saya tidak ingin mengasumsikan bahwa hal-hal tersebut merupakan kendala di {name}, sehingga saya ingin memahami kondisi yang sebenarnya terlebih dahulu."
5. Keterjelasan Niat: "Saat ini saya belum menentukan solusi maupun topik penelitian secara spesifik. Saya hanya ingin memahami permasalahan nyata yang terjadi di lapangan sebagai bahan pertimbangan penelitian."
6. Jaminan Kerahasiaan: "Tidak perlu memberikan data yang bersifat rahasia. Jika Bapak/Ibu berkenan sharing sedikit mengenai kendala yang pernah atau sedang dihadapi, saya akan sangat terbantu."
7. Penutup Sopan: "Terima kasih atas waktu dan perhatiannya, Bapak/Ibu."

--- INSTRUKSI DAN BATASAN KHUSUS TAMBAHAN DARI PENGGUNA (DO & DON'T) ---
{prompt_context_text}

--- DATA INPUT ---
- Nama Bisnis: {name}
- Kategori Usaha: {category}
- Alamat/Lokasi: {address}
- Konteks Tambahan: {context}
- Nama Mahasiswa: {student_name}
- Jurusan: {major}
- Universitas: {university} (jika kosong, jangan sebutkan nama universitas)
- Saluran Komunikasi: {channel} (whatsapp / email)

--- INSTRUKSI KHUSUS SALURAN ---
1. Jika saluran = 'whatsapp':
   - Pertahankan nada natural, ramah, dan santun.
   - Buat format pesan ringkas dan mudah dibaca di smartphone.
   - Kosongkan field "subject" (karena WhatsApp tidak butuh subjek).

2. Jika saluran = 'email':
   - Gunakan format email permohonan yang rapi dan profesional.
   - Buat "subject" email yang jelas (misal: "Permohonan Diskusi Awal Riset Skripsi - {name}").

Berikan output dalam format JSON PERSIS seperti berikut (Bahasa Indonesia):
{{
    "subject": "Subjek email (kosongkan jika whatsapp)",
    "message": "Isi lengkap pesan yang sudah dipersonalisasi berdasarkan Master of Truth dan Instruksi Khusus Pengguna"
}}"""


class OpenAIProvider(AIProvider):
    def __init__(self) -> None:
        self._settings = get_settings()

    async def is_available(self) -> bool:
        if not self._settings.ai_enabled:
            return False
        if not self._settings.ai_api_key:
            return False
        return True

    async def analyze_business(
        self,
        business_name: str,
        business_data: dict[str, Any],
        website_data: dict[str, Any] | None = None,
    ) -> AIAnalysisResult:
        if not await self.is_available():
            return AIAnalysisResult(
                business_id=0,
                operational_problems="AI tidak aktif atau konfigurasi API Key belum diset.",
                model_used="none",
            )

        website_analysis = ""
        if website_data:
            website_analysis = f"""Analisis Website:
Judul Website: {website_data.get('title', 'N/A')}
Deskripsi: {website_data.get('meta_description', 'N/A')}
Layanan/Menu ditemukan: {', '.join(website_data.get('services', [])[:5]) or 'N/A'}
Fitur Formulir: {'Ada' if website_data.get('has_forms') else 'Tidak'}
Fitur Booking: {'Ada' if website_data.get('has_booking') else 'Tidak'}
Fitur E-commerce: {'Ada' if website_data.get('has_ecommerce') else 'Tidak'}
Indikator Teknologi: {', '.join(website_data.get('tech_indicators', [])[:5]) or 'N/A'}
Tautan Sosial Media: {len(website_data.get('social_links', []))} tautan ditemukan"""
        else:
            website_analysis = "Tidak ada data website yang terdeteksi."

        prompt = ANALYSIS_PROMPT_ID.format(
            name=business_name,
            category=business_data.get("category", "Umum"),
            address=business_data.get("address", "-"),
            phone=business_data.get("phone", "-"),
            website=business_data.get("website", "-"),
            rating=business_data.get("rating", "-"),
            review_count=business_data.get("review_count", "-"),
            website_analysis=website_analysis,
        )

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self._settings.ai_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._settings.ai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self._settings.ai_model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "Anda adalah asisten analis riset dan skripsi di Indonesia. Semua respons wajib berupa JSON valid dalam Bahasa Indonesia.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.3,
                        "max_tokens": 1600,
                        "stream": False,
                    },
                )
                response.raise_for_status()
                data = response.json()

                content = data["choices"][0]["message"]["content"]
                tokens_used = data.get("usage", {}).get("total_tokens", 0)

                content = content.strip()
                if content.startswith("```"):
                    lines = content.splitlines()
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].strip().endswith("```"):
                        lines = lines[:-1]
                    content = "\n".join(lines).strip()

                result_data = json.loads(content)

                topics = result_data.get("research_topics", [])
                if isinstance(topics, str):
                    topics = [t.strip() for t in topics.split("\n") if t.strip()]

                questions = result_data.get("validation_questions", [])
                if isinstance(questions, str):
                    questions = [q.strip() for q in questions.split("\n") if q.strip()]

                return AIAnalysisResult(
                    business_id=0,
                    operational_problems=result_data.get("operational_problems"),
                    info_system_opportunities=result_data.get("info_system_opportunities"),
                    research_relevance=result_data.get("research_relevance"),
                    research_topics=topics[:5],
                    validation_questions=questions[:5],
                    model_used=self._settings.ai_model,
                    tokens_used=tokens_used,
                )

        except json.JSONDecodeError as e:
            logger.error("Failed to parse AI response as JSON: %s", e)
            return AIAnalysisResult(
                business_id=0,
                operational_problems="Format respons AI tidak valid JSON. Silakan coba lagi.",
                model_used=self._settings.ai_model,
            )
        except httpx.HTTPStatusError as e:
            logger.error("AI API error: %s", e.response.status_code)
            return AIAnalysisResult(
                business_id=0,
                operational_problems=f"Kesalahan API AI: status HTTP {e.response.status_code}",
                model_used=self._settings.ai_model,
            )
        except Exception as e:
            logger.error("AI analysis failed: %s", e)
            return AIAnalysisResult(
                business_id=0,
                operational_problems=f"Analisis gagal: {type(e).__name__}",
                model_used=self._settings.ai_model,
            )

    async def generate_personalized_outreach(
        self,
        business_name: str,
        category: str,
        address: str,
        context: str = "",
        channel: str = "whatsapp",
        student_name: str = "Vega Setiawan",
        major: str = "S1 Sistem Informasi",
        university: str | None = None,
        prompt_context: str | None = None,
    ) -> dict[str, str]:
        univ_str = (university or "").strip()
        univ_text = f" dari {univ_str}" if univ_str else ""
        prompt_context_text = f"Batasan & Catatan Pengguna: {prompt_context.strip()}" if prompt_context and prompt_context.strip() else "Tidak ada batasan khusus tambahan."

        if not await self.is_available():
            default_body = (
                f"Selamat sore Bapak/Ibu, perkenalkan saya {student_name}, mahasiswa {major}{univ_text}.\n\n"
                f"Saya menemukan {business_name} melalui Google Maps dan melihat informasi mengenai layanan serta kontak yang tersedia. "
                f"Saat ini saya sedang melakukan riset awal untuk memahami permasalahan nyata yang dihadapi bisnis sebagai persiapan penelitian skripsi.\n\n"
                f"Jika Bapak/Ibu tidak keberatan, saya ingin bertanya apakah dalam operasional {business_name} terdapat proses atau kegiatan yang saat ini masih menjadi kendala, memakan waktu, sering dilakukan secara manual, atau menurut Bapak/Ibu masih dapat dibuat lebih efektif.\n\n"
                f"Namun, saya tidak ingin mengasumsikan bahwa hal-hal tersebut merupakan kendala di {business_name}, sehingga saya ingin memahami kondisi yang sebenarnya terlebih dahulu.\n\n"
                f"Saat ini saya belum menentukan solusi maupun topik penelitian secara spesifik. Saya hanya ingin memahami permasalahan nyata yang terjadi di lapangan sebagai bahan pertimbangan penelitian.\n\n"
                f"Tidak perlu memberikan data yang bersifat rahasia. Jika Bapak/Ibu berkenan sharing sedikit mengenai kendala yang pernah atau sedang dihadapi, saya akan sangat terbantu.\n\n"
                f"Terima kasih atas waktu dan perhatiannya, Bapak/Ibu."
            )
            return {"subject": f"Permohonan Riset Skripsi - {business_name}", "message": default_body}

        prompt = OUTREACH_PROMPT.format(
            name=business_name,
            category=category or "Umum",
            address=address or "-",
            context=context or "Digitalisasi proses bisnis, sistem informasi, dan efisiensi operasional",
            student_name=student_name,
            major=major or "S1 Sistem Informasi",
            university=univ_str,
            university_phrase=univ_text,
            prompt_context_text=prompt_context_text,
            channel=channel,
        )

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(
                    f"{self._settings.ai_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._settings.ai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self._settings.ai_model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "Anda adalah asisten permohonan riset skripsi berbahasa Indonesia. Respons WAJIB berupa format JSON valid.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.4,
                        "max_tokens": 1000,
                        "stream": False,
                    },
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()

                if content.startswith("```"):
                    lines = content.splitlines()
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].strip().endswith("```"):
                        lines = lines[:-1]
                    content = "\n".join(lines).strip()

                parsed = json.loads(content)
                return {
                    "subject": parsed.get("subject", f"Permohonan Riset - {business_name}"),
                    "message": parsed.get("message", ""),
                }
        except Exception as e:
            logger.error("Failed to generate personalized outreach: %s", e)
            return {
                "subject": f"Permohonan Riset Skripsi - {business_name}",
                "message": (
                    f"Selamat sore Bapak/Ibu, perkenalkan saya {student_name}, mahasiswa {major}{univ_text}.\n\n"
                    f"Saya menemukan {business_name} melalui Google Maps dan melihat informasi mengenai layanan serta kontak yang tersedia. "
                    f"Saat ini saya sedang melakukan riset awal untuk memahami permasalahan nyata yang dihadapi bisnis sebagai persiapan penelitian skripsi.\n\n"
                    f"Jika Bapak/Ibu tidak keberatan, saya ingin bertanya apakah dalam operasional {business_name} terdapat proses atau kegiatan yang saat ini masih menjadi kendala, memakan waktu, sering dilakukan secara manual, atau menurut Bapak/Ibu masih dapat dibuat lebih efektif.\n\n"
                    f"Namun, saya tidak mengasumsikan hal tersebut merupakan kendala di {business_name}, sehingga saya ingin memahami kondisi yang sebenarnya terlebih dahulu.\n\n"
                    f"Terima kasih atas waktu dan perhatiannya, Bapak/Ibu."
                ),
            }
