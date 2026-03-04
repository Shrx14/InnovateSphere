import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Github, ExternalLink, Sparkles, Lightbulb, Target } from 'lucide-react';
import { fadeIn, staggerContainer } from '@/lib/motion';

const team = [
    {
        name: 'Shreyas S',
        role: 'AI & Backend Engineer',
        github: 'https://github.com/Shrx14',
        username: 'Shrx14',
    },
    {
        name: 'Bethuel S',
        role: 'Frontend & UI Design',
        github: 'https://github.com/Bethuel-Shilesh',
        username: 'Bethuel-Shilesh',
    },
    {
        name: 'Vedant P',
        role: 'Integration & Testing',
        github: 'https://github.com/VedantPatil22',
        username: 'VedantPatil22',
    },
];

const values = [
    {
        icon: Sparkles,
        title: 'Evidence-First',
        description: 'Every idea is backed by real research papers and credible sources — not assumptions.',
    },
    {
        icon: Target,
        title: 'Measurable Novelty',
        description: 'Our scoring engine quantifies how original your idea is against existing work.',
    },
    {
        icon: Lightbulb,
        title: 'Accessible Innovation',
        description: 'Lowering the barrier to high-quality research ideation for everyone.',
    },
];

const AboutPage = () => {
    return (
        <div className="min-h-screen dark:bg-neutral-950/0 relative">
            <div className="relative z-10 max-w-5xl mx-auto px-6 py-24 md:py-32">
                {/* Hero */}
                <motion.div
                    variants={staggerContainer}
                    initial="hidden"
                    animate="visible"
                    className="mb-20"
                >
                    <motion.p variants={fadeIn} className="text-xs uppercase tracking-widest text-indigo-400 mb-4 font-semibold">
                        About Us
                    </motion.p>
                    <motion.h1 variants={fadeIn} className="text-4xl md:text-5xl font-display font-bold dark:text-white text-neutral-900 mb-6">
                        Building the future of <span className="text-indigo-400">research ideation</span>
                    </motion.h1>
                    <motion.p variants={fadeIn} className="text-lg dark:text-neutral-300 text-neutral-600 leading-relaxed max-w-3xl">
                        InnovateSphere was born from a simple observation: the gap between having a research question
                        and finding a genuinely novel, feasible project idea is enormous. We built a platform that
                        bridges that gap using AI, real evidence, and rigorous scoring — so researchers and builders
                        can focus on what matters: creating impact.
                    </motion.p>
                </motion.div>

                {/* Values */}
                <motion.div
                    variants={staggerContainer}
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true }}
                    className="mb-24"
                >
                    <motion.h2 variants={fadeIn} className="text-2xl font-display font-semibold dark:text-white text-neutral-900 mb-10">
                        What drives us
                    </motion.h2>
                    <div className="grid md:grid-cols-3 gap-6">
                        {values.map((v) => (
                            <motion.div
                                key={v.title}
                                variants={fadeIn}
                                className="p-6 rounded-2xl dark:bg-neutral-900/60 bg-white/60 border dark:border-neutral-800/50 border-neutral-200 backdrop-blur-sm"
                            >
                                <v.icon className="w-8 h-8 text-indigo-400 mb-4" />
                                <h3 className="text-lg font-semibold dark:text-white text-neutral-900 mb-2">{v.title}</h3>
                                <p className="text-sm dark:text-neutral-400 text-neutral-500 leading-relaxed">{v.description}</p>
                            </motion.div>
                        ))}
                    </div>
                </motion.div>

                {/* Team */}
                <motion.div
                    variants={staggerContainer}
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true }}
                >
                    <motion.h2 variants={fadeIn} className="text-2xl font-display font-semibold dark:text-white text-neutral-900 mb-3">
                        The team
                    </motion.h2>
                    <motion.p variants={fadeIn} className="dark:text-neutral-400 text-neutral-500 mb-10 max-w-2xl">
                        A collaborative effort by engineering students passionate about making innovation more
                        systematic and accessible.
                    </motion.p>
                    <div className="grid md:grid-cols-3 gap-6">
                        {team.map((member) => (
                            <motion.div
                                key={member.name}
                                variants={fadeIn}
                                whileHover={{ y: -4 }}
                                className="p-6 rounded-2xl dark:bg-neutral-900/60 bg-white/60 border dark:border-neutral-800/50 border-neutral-200 backdrop-blur-sm group"
                            >
                                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/20 flex items-center justify-center mb-4">
                                    <span className="text-lg font-display font-bold text-indigo-300">
                                        {member.name.split(' ').map(n => n[0]).join('')}
                                    </span>
                                </div>
                                <h3 className="text-lg font-semibold dark:text-white text-neutral-900 mb-1">{member.name}</h3>
                                <p className="text-sm dark:text-neutral-500 text-neutral-400 mb-4">{member.role}</p>
                                <a
                                    href={member.github}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-2 text-sm dark:text-neutral-400 text-neutral-500 hover:text-indigo-300 transition group"
                                >
                                    <Github className="w-4 h-4" />
                                    {member.username}
                                    <ExternalLink className="w-3 h-3 opacity-0 group-hover:opacity-100 transition" />
                                </a>
                            </motion.div>
                        ))}
                    </div>
                </motion.div>
            </div>
        </div>
    );
};

export default AboutPage;
