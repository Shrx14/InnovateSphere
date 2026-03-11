import React from 'react';
import { motion } from 'framer-motion';
import { fadeIn, staggerContainer } from '@/lib/motion';

const sections = [
    {
        title: '1. Acceptance of Terms',
        content: `By accessing or using InnovateSphere ("the Platform"), you agree to be bound by these Terms of Service. If you do not agree to these terms, you may not use the Platform. We reserve the right to modify these terms at any time, and your continued use constitutes acceptance of any changes.`,
    },
    {
        title: '2. Account Registration',
        content: `To use certain features, you must create an account with a valid email address and password. You are responsible for:
• Maintaining the confidentiality of your account credentials
• All activity that occurs under your account
• Notifying us immediately of any unauthorized use

We reserve the right to suspend or terminate accounts that violate these terms.`,
    },
    {
        title: '3. Acceptable Use',
        content: `You agree not to use InnovateSphere to:
• Generate, submit, or distribute content that is illegal, abusive, or infringes on the rights of others
• Attempt to gain unauthorized access to the Platform or its systems
• Circumvent security measures, rate limits, or access controls
• Use automated tools (bots, scrapers) to access the Platform without prior written permission
• Submit misleading or spam-like content to manipulate scores or rankings

We reserve the right to remove content and suspend accounts that violate these guidelines.`,
    },
    {
        title: '4. Intellectual Property',
        content: `Ideas and content you create through InnovateSphere remain your intellectual property. However, by using the Platform, you grant us a non-exclusive, worldwide, royalty-free license to display, distribute, and use your public content for the purpose of operating and promoting the Platform.

The InnovateSphere name, logo, and platform design are our proprietary property and may not be used without permission.`,
    },
    {
        title: '5. AI-Generated Content',
        content: `InnovateSphere uses artificial intelligence to generate idea suggestions, novelty scores, and quality assessments. While we strive for accuracy, AI-generated content:
• May contain errors, inaccuracies, or outdated information
• Should not be relied upon as the sole basis for academic, business, or legal decisions
• Does not constitute professional advice

You are responsible for independently verifying any information or suggestions provided by the Platform.`,
    },
    {
        title: '6. Novelty and Quality Scores',
        content: `Scores provided by InnovateSphere are estimates based on our algorithms and available data. They:
• Are not guarantees of novelty, patentability, or commercial viability
• May change as our algorithms and datasets evolve
• Should be used as one factor among many in your decision-making process`,
    },
    {
        title: '7. Limitation of Liability',
        content: `InnovateSphere is provided "as is" without warranties of any kind, express or implied. We do not guarantee that the Platform will be uninterrupted, error-free, or secure.

To the maximum extent permitted by law, InnovateSphere and its team shall not be liable for any indirect, incidental, special, consequential, or punitive damages arising from your use of the Platform.`,
    },
    {
        title: '8. Termination',
        content: `We may suspend or terminate your access to the Platform at any time, with or without cause, and with or without notice. Upon termination, your right to use the Platform ceases immediately. Sections regarding intellectual property, limitation of liability, and dispute resolution survive termination.`,
    },
    {
        title: '9. Governing Law',
        content: `These Terms shall be governed by and construed in accordance with applicable laws. Any disputes arising from these terms or your use of the Platform shall be resolved through good-faith negotiation before pursuing formal legal remedies.`,
    },
    {
        title: '10. Contact',
        content: `For questions about these Terms of Service, please contact us at support@innovatesphere.com.`,
    },
];

const TermsPage = () => {
    return (
        <div className="min-h-screen bg-neutral-950/0 relative">
            <div className="relative z-10 max-w-3xl mx-auto px-6 py-24 md:py-32">
                <motion.div
                    variants={staggerContainer}
                    initial="hidden"
                    animate="visible"
                >
                    <motion.p variants={fadeIn} className="text-xs uppercase tracking-widest text-indigo-400 mb-4 font-semibold">
                        Legal
                    </motion.p>
                    <motion.h1 variants={fadeIn} className="text-4xl md:text-5xl font-display font-bold text-white mb-4">
                        Terms of Service
                    </motion.h1>
                    <motion.p variants={fadeIn} className="text-sm text-neutral-500 mb-12">
                        Last updated: February 2026
                    </motion.p>

                    <motion.p variants={fadeIn} className="text-neutral-300 leading-relaxed mb-12">
                        These Terms of Service govern your use of InnovateSphere. Please read them carefully before using the Platform.
                    </motion.p>

                    <div className="space-y-10">
                        {sections.map((section) => (
                            <motion.div key={section.title} variants={fadeIn}>
                                <h2 className="text-lg font-display font-semibold text-white mb-3">{section.title}</h2>
                                <div className="text-sm text-neutral-400 leading-relaxed whitespace-pre-line">
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

export default TermsPage;
