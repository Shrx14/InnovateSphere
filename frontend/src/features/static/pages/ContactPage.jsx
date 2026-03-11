import React from 'react';
import { motion } from 'framer-motion';
import { Mail, Clock, HelpCircle, MessageSquare } from 'lucide-react';
import { fadeIn, staggerContainer } from '@/lib/motion';

const faqs = [
    {
        q: 'How do I create an account?',
        a: 'Click "Get Started" on the homepage or navigate to the registration page. You\'ll need an email, username, and password.',
    },
    {
        q: 'Is InnovateSphere free to use?',
        a: 'Yes. InnovateSphere is currently free for all users. We may introduce premium features in the future, but the core platform will remain accessible.',
    },
    {
        q: 'How are novelty scores calculated?',
        a: 'Our scoring engine cross-references your idea against research papers, patents, and existing projects to quantify originality on a standardized scale.',
    },
    {
        q: 'Can I export or share my ideas?',
        a: 'You can make your ideas public so they appear on the Explore page. Direct export features are planned for a future release.',
    },
    {
        q: 'I found a bug. How do I report it?',
        a: 'Please email us at the address below with a description of the issue, including any screenshots if possible.',
    },
];

const ContactPage = () => {
    return (
        <div className="min-h-screen bg-neutral-950/0 relative">
            <div className="relative z-10 max-w-5xl mx-auto px-6 py-24 md:py-32">
                {/* Header */}
                <motion.div
                    variants={staggerContainer}
                    initial="hidden"
                    animate="visible"
                    className="mb-16"
                >
                    <motion.p variants={fadeIn} className="text-xs uppercase tracking-widest text-indigo-400 mb-4 font-semibold">
                        Contact
                    </motion.p>
                    <motion.h1 variants={fadeIn} className="text-4xl md:text-5xl font-display font-bold text-white mb-6">
                        Get in touch
                    </motion.h1>
                    <motion.p variants={fadeIn} className="text-lg text-neutral-300 leading-relaxed max-w-2xl">
                        Have a question, feature request, or just want to say hello? We'd love to hear from you.
                    </motion.p>
                </motion.div>

                <div className="grid lg:grid-cols-2 gap-12 mb-24">
                    {/* Contact cards */}
                    <motion.div
                        variants={staggerContainer}
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true }}
                        className="space-y-6"
                    >
                        <motion.div
                            variants={fadeIn}
                            className="p-6 rounded-2xl bg-neutral-900/60 border border-neutral-800/50 backdrop-blur-sm"
                        >
                            <Mail className="w-6 h-6 text-indigo-400 mb-3" />
                            <h3 className="text-lg font-semibold text-white mb-2">Email Support</h3>
                            <p className="text-sm text-neutral-400 mb-4">
                                For general inquiries, bug reports, or feature requests:
                            </p>
                            <a
                                href="mailto:support@innovatesphere.com"
                                className="text-indigo-400 hover:text-indigo-300 font-medium transition"
                            >
                                support@innovatesphere.com
                            </a>
                        </motion.div>

                        <motion.div
                            variants={fadeIn}
                            className="p-6 rounded-2xl bg-neutral-900/60 border border-neutral-800/50 backdrop-blur-sm"
                        >
                            <Clock className="w-6 h-6 text-purple-400 mb-3" />
                            <h3 className="text-lg font-semibold text-white mb-2">Response Time</h3>
                            <p className="text-sm text-neutral-400">
                                We typically respond within 24–48 hours on business days. For urgent issues,
                                please include "URGENT" in your subject line.
                            </p>
                        </motion.div>

                        <motion.div
                            variants={fadeIn}
                            className="p-6 rounded-2xl bg-neutral-900/60 border border-neutral-800/50 backdrop-blur-sm"
                        >
                            <MessageSquare className="w-6 h-6 text-emerald-400 mb-3" />
                            <h3 className="text-lg font-semibold text-white mb-2">Feature Requests</h3>
                            <p className="text-sm text-neutral-400">
                                We actively shape our roadmap based on user feedback.
                                Tell us what you'd like to see in InnovateSphere — every suggestion is reviewed by the team.
                            </p>
                        </motion.div>
                    </motion.div>

                    {/* FAQ */}
                    <motion.div
                        variants={staggerContainer}
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true }}
                    >
                        <motion.div variants={fadeIn} className="flex items-center gap-2 mb-6">
                            <HelpCircle className="w-5 h-5 text-indigo-400" />
                            <h2 className="text-xl font-display font-semibold text-white">Frequently Asked Questions</h2>
                        </motion.div>
                        <div className="space-y-4">
                            {faqs.map((faq, i) => (
                                <motion.div
                                    key={i}
                                    variants={fadeIn}
                                    className="p-5 rounded-xl bg-neutral-900/40 border border-neutral-800/40"
                                >
                                    <h4 className="text-sm font-semibold text-neutral-200 mb-2">{faq.q}</h4>
                                    <p className="text-sm text-neutral-400 leading-relaxed">{faq.a}</p>
                                </motion.div>
                            ))}
                        </div>
                    </motion.div>
                </div>
            </div>
        </div>
    );
};

export default ContactPage;
