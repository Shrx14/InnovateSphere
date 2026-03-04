import React from 'react';
import { motion } from 'framer-motion';
import { fadeIn, staggerContainer } from '@/lib/motion';

const sections = [
    {
        title: '1. Information We Collect',
        content: `When you create an account, we collect your email address, username, and chosen skill level. When you use the platform, we collect the ideas you generate, novelty scores, search queries, and interaction data such as page views and timestamps.

We do not collect payment information, government-issued IDs, or sensitive personal data beyond what is described above.`,
    },
    {
        title: '2. How We Use Your Information',
        content: `We use your information to:
• Provide, maintain, and improve the InnovateSphere platform
• Generate and score research ideas tailored to your preferences
• Display aggregate analytics and domain statistics on public pages
• Communicate with you about your account and respond to inquiries
• Detect and prevent abuse, spam, and unauthorized access

We do not sell, rent, or share your personal information with third-party advertisers.`,
    },
    {
        title: '3. Data Storage and Security',
        content: `Your data is stored in secure, industry-standard cloud databases. We implement encryption in transit (HTTPS/TLS) and follow security best practices for access control and authentication.

While we take reasonable measures to protect your data, no system is perfectly secure. You are responsible for maintaining the security of your account credentials.`,
    },
    {
        title: '4. Your Content and Ideas',
        content: `Ideas you generate remain your intellectual property. By making an idea "public," you grant InnovateSphere a non-exclusive license to display that idea on the platform, including in aggregate statistics and on the Explore page.

You may delete your ideas at any time through your dashboard.`,
    },
    {
        title: '5. Cookies and Tracking',
        content: `We use essential cookies to maintain your session and authentication state. We may use analytics tools to understand usage patterns and improve the platform. These tools collect anonymized, aggregate data only.

You can disable cookies in your browser settings, but some platform features may not work correctly without them.`,
    },
    {
        title: '6. Third-Party Services',
        content: `InnovateSphere integrates with third-party AI services to generate ideas and perform novelty scoring. These services process your inputs in accordance with their own privacy policies. We do not share your personal account information with these services — only the content of your idea generation requests.`,
    },
    {
        title: '7. Data Retention',
        content: `We retain your account data for as long as your account is active. If you request account deletion, we will remove your personal information within 30 days. Some anonymized, aggregate data may be retained for analytics purposes.`,
    },
    {
        title: '8. Children\'s Privacy',
        content: `InnovateSphere is not directed at individuals under the age of 13. We do not knowingly collect personal information from children. If we learn that we have collected data from a child under 13, we will delete it promptly.`,
    },
    {
        title: '9. Changes to This Policy',
        content: `We may update this Privacy Policy from time to time. We will notify registered users of material changes via email or an in-app notice. Your continued use of the platform after changes constitutes acceptance of the updated policy.`,
    },
    {
        title: '10. Contact Us',
        content: `If you have questions about this Privacy Policy or wish to exercise your data rights, please contact us at support@innovatesphere.com.`,
    },
];

const PrivacyPage = () => {
    return (
        <div className="min-h-screen dark:bg-neutral-950/0 relative">
            <div className="relative z-10 max-w-3xl mx-auto px-6 py-24 md:py-32">
                <motion.div
                    variants={staggerContainer}
                    initial="hidden"
                    animate="visible"
                >
                    <motion.p variants={fadeIn} className="text-xs uppercase tracking-widest text-indigo-400 mb-4 font-semibold">
                        Legal
                    </motion.p>
                    <motion.h1 variants={fadeIn} className="text-4xl md:text-5xl font-display font-bold dark:text-white text-neutral-900 mb-4">
                        Privacy Policy
                    </motion.h1>
                    <motion.p variants={fadeIn} className="text-sm dark:text-neutral-500 text-neutral-400 mb-12">
                        Last updated: February 2026
                    </motion.p>

                    <motion.p variants={fadeIn} className="dark:text-neutral-300 text-neutral-600 leading-relaxed mb-12">
                        At InnovateSphere, we take your privacy seriously. This policy explains what information we collect,
                        how we use it, and the choices you have regarding your data.
                    </motion.p>

                    <div className="space-y-10">
                        {sections.map((section) => (
                            <motion.div key={section.title} variants={fadeIn}>
                                <h2 className="text-lg font-display font-semibold dark:text-white text-neutral-900 mb-3">{section.title}</h2>
                                <div className="text-sm dark:text-neutral-400 text-neutral-500 leading-relaxed whitespace-pre-line">
                                    {section.content}
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </motion.div>
            </div>
        </div>
    );
};

export default PrivacyPage;
