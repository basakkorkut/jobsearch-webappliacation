-- ============================================================
-- SE4458 JobSearch — Initial Migration
-- Run this in Supabase SQL Editor (single execution)
-- ============================================================

-- ============================================================
-- EXTENSIONS
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "pgcrypto";


-- ============================================================
-- TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS public.companies (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT        NOT NULL,
    description TEXT,
    logo_url    TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.job_postings (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id          UUID        NOT NULL REFERENCES public.companies(id) ON DELETE CASCADE,
    title               TEXT        NOT NULL,
    description         TEXT        NOT NULL,
    country             TEXT        NOT NULL,
    city                TEXT        NOT NULL,
    town                TEXT,
    working_preference  TEXT        CHECK (working_preference IN ('remote', 'on_site', 'hybrid')),
    position_level      TEXT        CHECK (position_level IN ('junior', 'mid', 'senior', 'expert', 'intern')),
    department          TEXT,
    employment_type     TEXT        CHECK (employment_type IN ('full_time', 'part_time', 'contract', 'internship')),
    application_count   INTEGER     DEFAULT 0,
    created_by          UUID        REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.applications (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID        NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    job_posting_id  UUID        NOT NULL REFERENCES public.job_postings(id) ON DELETE CASCADE,
    applied_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, job_posting_id)
);

CREATE TABLE IF NOT EXISTS public.job_alerts (
    id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID        NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    keywords   TEXT        NOT NULL,
    country    TEXT,
    city       TEXT,
    town       TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- user_profiles: PK is auth.users.id (1-to-1)
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id         UUID        PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name  TEXT,
    role       TEXT        DEFAULT 'candidate' CHECK (role IN ('candidate', 'admin', 'company')),
    company_id UUID        REFERENCES public.companies(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);


-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_jobs_city_country ON public.job_postings(city, country);
CREATE INDEX IF NOT EXISTS idx_jobs_title        ON public.job_postings(title);
CREATE INDEX IF NOT EXISTS idx_jobs_created      ON public.job_postings(created_at DESC);


-- ============================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================

-- Auto-update updated_at on job_postings
CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS set_updated_at ON public.job_postings;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON public.job_postings
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();


-- Atomic application count increment (called from backend to avoid race conditions)
CREATE OR REPLACE FUNCTION public.increment_application_count(job_id UUID)
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE public.job_postings
    SET application_count = application_count + 1
    WHERE id = job_id;
END;
$$;


-- Auto-create user_profile row when a new Supabase auth user signs up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER   -- runs as postgres, bypasses RLS
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.user_profiles (id, full_name, role)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'full_name', ''),
        COALESCE(NEW.raw_user_meta_data->>'role', 'candidate')
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();


-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

-- companies
ALTER TABLE public.companies ENABLE ROW LEVEL SECURITY;

CREATE POLICY "companies_select_all"
    ON public.companies FOR SELECT
    USING (true);

CREATE POLICY "companies_insert_admin"
    ON public.companies FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.user_profiles
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

CREATE POLICY "companies_update_admin"
    ON public.companies FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles
            WHERE id = auth.uid() AND role = 'admin'
        )
    );


-- job_postings
ALTER TABLE public.job_postings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "job_postings_select_all"
    ON public.job_postings FOR SELECT
    USING (true);

CREATE POLICY "job_postings_insert_admin_company"
    ON public.job_postings FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.user_profiles
            WHERE id = auth.uid() AND role IN ('admin', 'company')
        )
    );

CREATE POLICY "job_postings_update_admin_company"
    ON public.job_postings FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles
            WHERE id = auth.uid() AND role IN ('admin', 'company')
        )
    );

CREATE POLICY "job_postings_delete_admin_company"
    ON public.job_postings FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles
            WHERE id = auth.uid() AND role IN ('admin', 'company')
        )
    );


-- applications
ALTER TABLE public.applications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "applications_select_own"
    ON public.applications FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "applications_insert_own"
    ON public.applications FOR INSERT
    WITH CHECK (auth.uid() = user_id);


-- job_alerts
ALTER TABLE public.job_alerts ENABLE ROW LEVEL SECURITY;

-- single policy covers all operations (USING for read/update/delete, WITH CHECK for insert/update)
CREATE POLICY "job_alerts_own"
    ON public.job_alerts
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);


-- user_profiles
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "user_profiles_select_own"
    ON public.user_profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "user_profiles_update_own"
    ON public.user_profiles FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);


-- ============================================================
-- SEED DATA
-- ============================================================

-- 5 Companies (fixed UUIDs for reproducible FK references)
INSERT INTO public.companies (id, name, description) VALUES
    ('11111111-1111-1111-1111-111111111111', 'Trendyol',     'Türkiye''nin en büyük e-ticaret platformu'),
    ('22222222-2222-2222-2222-222222222222', 'Getir',         'Dakikalar içinde teslimat platformu'),
    ('33333333-3333-3333-3333-333333333333', 'Yemeksepeti',   'Yemek ve market teslimat platformu'),
    ('44444444-4444-4444-4444-444444444444', 'Hepsiburada',   'Çok kategorili e-ticaret marketi'),
    ('55555555-5555-5555-5555-555555555555', 'Peak Games',    'Uluslararası mobil oyun stüdyosu')
ON CONFLICT (id) DO NOTHING;


-- 20 Job Postings
-- Istanbul: 8 | Izmir: 4 | Ankara: 3 | Bursa: 3 | Antalya: 2
INSERT INTO public.job_postings
    (company_id, title, description, country, city, town, working_preference, position_level, department, employment_type)
VALUES

-- ── Istanbul (8) ──────────────────────────────────────────
(
    '11111111-1111-1111-1111-111111111111',
    'Senior Backend Engineer',
    'Trendyol backend ekibinde milyonlarca kullanıcıya hizmet eden yüksek trafikli sistemler geliştiriyoruz. Java/Kotlin veya Go ile microservice mimarisinde 5+ yıl deneyim arıyoruz.',
    'Turkey', 'Istanbul', 'Kadıköy',
    'hybrid', 'senior', 'Engineering', 'full_time'
),
(
    '11111111-1111-1111-1111-111111111111',
    'Frontend Developer',
    'React ve TypeScript ile milyonlarca kullanıcıya dokunacak arayüzler geliştir. Next.js, performance optimizasyon ve A/B test deneyimi olan adaylar tercih edilir.',
    'Turkey', 'Istanbul', 'Beşiktaş',
    'hybrid', 'mid', 'Engineering', 'full_time'
),
(
    '22222222-2222-2222-2222-222222222222',
    'iOS Developer',
    'Swift ve SwiftUI ile Getir iOS uygulamasını geliştir. Push notification, harita entegrasyonu ve gerçek zamanlı sipariş takibi konularında deneyim arıyoruz.',
    'Turkey', 'Istanbul', 'Şişli',
    'on_site', 'mid', 'Mobile', 'full_time'
),
(
    '22222222-2222-2222-2222-222222222222',
    'Data Analyst',
    'Getir operasyon ve büyüme verilerini analiz et, dashboard''lar oluştur. SQL, Python (pandas) ve BI araçları (Tableau/Looker) konusunda deneyim gereklidir.',
    'Turkey', 'Istanbul', 'Maslak',
    'hybrid', 'junior', 'Data & Analytics', 'full_time'
),
(
    '33333333-3333-3333-3333-333333333333',
    'DevOps Engineer',
    'Kubernetes, Helm ve Terraform ile bulut altyapısını yönet. AWS veya GCP üzerinde CI/CD pipeline kurulumu ve site reliability engineering deneyimi arıyoruz.',
    'Turkey', 'Istanbul', 'Ataşehir',
    'remote', 'senior', 'Infrastructure', 'full_time'
),
(
    '33333333-3333-3333-3333-333333333333',
    'Backend Developer (Python)',
    'FastAPI ve Django ile Yemeksepeti''nin sipariş ve ödeme servislerini geliştir. PostgreSQL, Redis ve Kafka konusunda deneyim tercih edilir.',
    'Turkey', 'Istanbul', 'Kadıköy',
    'hybrid', 'mid', 'Engineering', 'full_time'
),
(
    '44444444-4444-4444-4444-444444444444',
    'ML Engineer',
    'Hepsiburada öneri sistemi, fiyatlandırma ve müşteri segmentasyon modellerini geliştir ve üretimleştir. PyTorch/TensorFlow, MLflow, Spark konularında deneyim gereklidir.',
    'Turkey', 'Istanbul', 'Sarıyer',
    'hybrid', 'senior', 'AI / ML', 'full_time'
),
(
    '55555555-5555-5555-5555-555555555555',
    'Unity Game Developer',
    'Peak Games hyper-casual ve casual oyun portföyü için Unity''de yeni oyunlar ve feature''lar geliştir. C#, shader programlama ve mobile performance optimizasyonu deneyimi aranıyor.',
    'Turkey', 'Istanbul', 'Levent',
    'on_site', 'mid', 'Game Development', 'full_time'
),

-- ── Izmir (4) ─────────────────────────────────────────────
(
    '44444444-4444-4444-4444-444444444444',
    'Junior Web Developer',
    'React ve Node.js ile Hepsiburada satıcı paneli ve iç araçlarını geliştir. Yazılım mühendisliği bölümü yeni mezunları veya 1 yıl deneyimliler başvurabilir.',
    'Turkey', 'Izmir', 'Alsancak',
    'hybrid', 'junior', 'Engineering', 'full_time'
),
(
    '11111111-1111-1111-1111-111111111111',
    'Product Manager',
    'Trendyol İzmir ofisinde satıcı deneyimi ürününü yönet. Veri odaklı karar alma, roadmap yönetimi ve çapraz fonksiyonel ekiplerle çalışma deneyimi arıyoruz.',
    'Turkey', 'Izmir', 'Konak',
    'hybrid', 'mid', 'Product', 'full_time'
),
(
    '22222222-2222-2222-2222-222222222222',
    'Frontend Developer (React)',
    'Getir web ve admin platformları için React, TypeScript ve GraphQL ile feature geliştir. Uzaktan çalışma imkânı mevcuttur.',
    'Turkey', 'Izmir', 'Bornova',
    'remote', 'mid', 'Engineering', 'full_time'
),
(
    '55555555-5555-5555-5555-555555555555',
    'QA Engineer',
    'Peak Games oyunları için manuel ve otomatik (Appium/Selenium) test süreçlerini yönet. Bug tracking, test plan yazımı ve agile metodoloji deneyimi gereklidir.',
    'Turkey', 'Izmir', 'Karşıyaka',
    'hybrid', 'junior', 'Quality Assurance', 'full_time'
),

-- ── Ankara (3) ────────────────────────────────────────────
(
    '33333333-3333-3333-3333-333333333333',
    'Cloud Architect',
    'Azure ve AWS üzerinde enterprise ölçekli bulut mimarisi tasarla. Well-Architected Framework, FinOps ve multi-cloud strateji konularında 8+ yıl deneyim aranıyor.',
    'Turkey', 'Ankara', 'Çankaya',
    'hybrid', 'expert', 'Infrastructure', 'full_time'
),
(
    '44444444-4444-4444-4444-444444444444',
    'Software Engineer',
    'Hepsiburada lojistik ve depo yönetim sistemlerini geliştir. Java Spring Boot veya .NET ile backend geliştirme, PostgreSQL ve mesaj kuyruğu (Kafka/RabbitMQ) deneyimi aranıyor.',
    'Turkey', 'Ankara', 'Kızılay',
    'on_site', 'mid', 'Engineering', 'full_time'
),
(
    '11111111-1111-1111-1111-111111111111',
    'Data Scientist',
    'Trendyol fiyatlandırma ve talep tahminleme modellerini geliştir. İstatistik/matematik lisans veya yüksek lisans, Python ve ML pipeline deneyimi gereklidir.',
    'Turkey', 'Ankara', 'Söğütözü',
    'hybrid', 'senior', 'Data & Analytics', 'full_time'
),

-- ── Bursa (3) ─────────────────────────────────────────────
(
    '55555555-5555-5555-5555-555555555555',
    'Android Developer',
    'Kotlin ve Jetpack Compose ile Peak Games mobil oyun companion uygulamasını geliştir. Room, Coroutines ve Google Play Services konularında deneyim tercih edilir.',
    'Turkey', 'Bursa', 'Nilüfer',
    'hybrid', 'mid', 'Mobile', 'full_time'
),
(
    '22222222-2222-2222-2222-222222222222',
    'Backend Stajyeri',
    'Getir Bursa teknoloji ofisinde Python (FastAPI/Django) ile backend geliştirme stajı. Üniversite 3. veya 4. sınıf öğrencileri başvurabilir. Maaşlı tam zamanlı staj.',
    'Turkey', 'Bursa', 'Osmangazi',
    'on_site', 'intern', 'Engineering', 'internship'
),
(
    '33333333-3333-3333-3333-333333333333',
    'Full Stack Developer',
    'React ve Django REST Framework ile Yemeksepeti restoran partner portalı geliştir. TypeScript, REST API tasarımı ve CI/CD deneyimi aranıyor.',
    'Turkey', 'Bursa', 'Nilüfer',
    'hybrid', 'mid', 'Engineering', 'full_time'
),

-- ── Antalya (2) ───────────────────────────────────────────
(
    '44444444-4444-4444-4444-444444444444',
    'React Native Developer',
    'Hepsiburada mobil uygulamasında React Native ile cross-platform feature geliştir. Expo, Redux Toolkit ve native modül entegrasyonu konularında deneyim arıyoruz. Tamamen uzaktan çalışma.',
    'Turkey', 'Antalya', 'Kepez',
    'remote', 'mid', 'Mobile', 'full_time'
),
(
    '11111111-1111-1111-1111-111111111111',
    'DevOps Stajyeri',
    'Trendyol Antalya ofisinde Docker, Kubernetes ve CI/CD pipeline''ları öğren. Bilgisayar mühendisliği veya benzer bölüm öğrencileri için maaşlı yaz stajı.',
    'Turkey', 'Antalya', 'Muratpaşa',
    'on_site', 'intern', 'Infrastructure', 'internship'
);
