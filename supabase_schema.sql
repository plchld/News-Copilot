-- Supabase database schema for News Copilot
-- Run this in your Supabase SQL editor

-- Enable Row Level Security
ALTER TABLE auth.users ENABLE ROW LEVEL SECURITY;

-- User profiles table (extends Supabase auth.users)
CREATE TABLE public.user_profiles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    tier VARCHAR(50) DEFAULT 'free' CHECK (tier IN ('free', 'pro', 'premium', 'byok', 'admin')),
    api_key TEXT,
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    email_verified BOOLEAN DEFAULT true, -- Supabase handles verification
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Usage logs for analytics and rate limiting
CREATE TABLE public.usage_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    analysis_type VARCHAR(50) NOT NULL,
    article_url TEXT,
    tokens_used INTEGER DEFAULT 0,
    cost_usd DECIMAL(10,4) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Admin operations log
CREATE TABLE public.admin_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    admin_user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    action VARCHAR(100) NOT NULL,
    target_user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Row Level Security Policies

-- User profiles: Users can only see/edit their own profile
CREATE POLICY "Users can view own profile" ON public.user_profiles
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update own profile" ON public.user_profiles
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own profile" ON public.user_profiles
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Admin can see all profiles
CREATE POLICY "Admins can view all profiles" ON public.user_profiles
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles 
            WHERE user_id = auth.uid() AND tier = 'admin'
        )
    );

-- Usage logs: Users can only see their own logs
CREATE POLICY "Users can view own usage" ON public.usage_logs
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own usage" ON public.usage_logs
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Admin can see all usage logs
CREATE POLICY "Admins can view all usage" ON public.usage_logs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles 
            WHERE user_id = auth.uid() AND tier = 'admin'
        )
    );

-- Admin logs: Only admins can see
CREATE POLICY "Admins can view admin logs" ON public.admin_logs
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles 
            WHERE user_id = auth.uid() AND tier = 'admin'
        )
    );

-- Indexes for performance
CREATE INDEX idx_user_profiles_user_id ON public.user_profiles(user_id);
CREATE INDEX idx_user_profiles_email ON public.user_profiles(email);
CREATE INDEX idx_user_profiles_tier ON public.user_profiles(tier);
CREATE INDEX idx_usage_logs_user_id ON public.usage_logs(user_id);
CREATE INDEX idx_usage_logs_created_at ON public.usage_logs(created_at);
CREATE INDEX idx_usage_logs_analysis_type ON public.usage_logs(analysis_type);

-- Functions for admin operations

-- Get user statistics
CREATE OR REPLACE FUNCTION get_user_stats()
RETURNS TABLE (
    total_users BIGINT,
    free_users BIGINT,
    pro_users BIGINT,
    premium_users BIGINT,
    byok_users BIGINT,
    today_usage BIGINT,
    month_usage BIGINT
) 
LANGUAGE sql
SECURITY DEFINER
AS $$
    SELECT 
        (SELECT COUNT(*) FROM public.user_profiles) as total_users,
        (SELECT COUNT(*) FROM public.user_profiles WHERE tier = 'free') as free_users,
        (SELECT COUNT(*) FROM public.user_profiles WHERE tier = 'pro') as pro_users,
        (SELECT COUNT(*) FROM public.user_profiles WHERE tier = 'premium') as premium_users,
        (SELECT COUNT(*) FROM public.user_profiles WHERE tier = 'byok') as byok_users,
        (SELECT COUNT(*) FROM public.usage_logs WHERE created_at >= CURRENT_DATE) as today_usage,
        (SELECT COUNT(*) FROM public.usage_logs WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)) as month_usage;
$$;

-- Get monthly usage stats
CREATE OR REPLACE FUNCTION get_monthly_usage_stats(target_user_id UUID)
RETURNS TABLE (
    basic_analysis BIGINT,
    deep_analysis BIGINT
)
LANGUAGE sql
SECURITY DEFINER
AS $$
    SELECT 
        COUNT(*) FILTER (WHERE analysis_type IN ('jargon', 'viewpoints')) as basic_analysis,
        COUNT(*) FILTER (WHERE analysis_type NOT IN ('jargon', 'viewpoints')) as deep_analysis
    FROM public.usage_logs 
    WHERE user_id = target_user_id 
    AND created_at >= DATE_TRUNC('month', CURRENT_DATE);
$$;

-- Triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_profiles_updated_at 
    BEFORE UPDATE ON public.user_profiles 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable real-time subscriptions (optional)
-- ALTER PUBLICATION supabase_realtime ADD TABLE public.user_profiles;
-- ALTER PUBLICATION supabase_realtime ADD TABLE public.usage_logs;