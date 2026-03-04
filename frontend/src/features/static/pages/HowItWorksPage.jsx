import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Search, Sparkles, BarChart3, Layers, ArrowRight } from 'lucide-react';
import { fadeIn, staggerContainer } from '@/lib/motion';

const steps = [
    {
        number: '01',
        icon: Layers,
        title: 'Choose a Domain',
        description: 'Select from 10+ research domains — AI, Healthcare, Blockchain, IoT, and more. The system tailors idea generation to your chosen field.',
        color: 'text-indigo-400',
        bg: 'from-indigo-500/20 to-indigo-500/5',
        border: 'border-indigo-500/20',
    },
    {
        number: '02',
        icon: Sparkles,
        title: 'AI Generates Ideas',
        description: 'Our AI engine synthesizes knowledge from research papers, industry trends, and existing solutions to propose novel project ideas with supporting evidence.',
        color: 'text-purple-400',
        bg: 'from-purple-500/20 to-purple-500/5',
        border: 'border-purple-500/20',
    },
    {
        number: '03',
        icon: Search,
        title: 'Novelty Scoring',
        description: 'Each idea is automatically scored against existing work. The system checks research databases and prior art to quantify how original your idea truly is.',
        color: 'text-emerald-400',
        bg: 'from-emerald-500/20 to-emerald-500/5',
        border: 'border-emerald-500/20',
    },
    {
        number: '04',
        icon: BarChart3,
        title: 'Quality Evaluation',
        description: 'Ideas are assessed on feasibility, impact potential, and technical depth. You get a clear quality score alongside the novelty rating — data-driven, not subjective.',
        color: 'text-amber-400',
        bg: 'from-amber-500/20 to-amber-500/5',
        border: 'border-amber-500/20',
    },
];

const HowItWorksPage = () => {
    return (
        <div className="min-h-screen dark:bg-neutral-950/0 relative">
            <div className="relative z-10 max-w-5xl mx-auto px-6 py-24 md:py-32">
                {/* Header */}
                <motion.div
                    variants={staggerContainer}
                    initial="hidden"
                    animate="visible"
                    className="mb-20 text-center"
                >
                    <motion.p variants={fadeIn} className="text-xs uppercase tracking-widest text-indigo-400 mb-4 font-semibold">
                        How It Works
                    </motion.p>
                    <motion.h1 variants={fadeIn} className="text-4xl md:text-5xl font-display font-bold dark:text-white text-neutral-900 mb-6">
                        From domain to <span className="text-indigo-400">scored idea</span>
                        <br />in minutes
                    </motion.h1>
                    <motion.p variants={fadeIn} className="text-lg dark:text-neutral-300 text-neutral-600 leading-relaxed max-w-2xl mx-auto">
                        InnovateSphere automates research ideation with a four-step pipeline that combines
                        AI generation, evidence retrieval, and rigorous scoring.
                    </motion.p>
                </motion.div>

                {/* Steps */}
                <motion.div
                    variants={staggerContainer}
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true }}
                    className="space-y-6 mb-20"
                >
                    {steps.map((step, i) => (
                        <motion.div
                            key={step.number}
                            variants={fadeIn}
                            className={`relative flex flex-col md:flex-row gap-6 p-8 rounded-2xl bg-gradient-to-r ${step.bg} border ${step.border} backdrop-blur-sm`}
                        >
                            <div className="flex-shrink-0">
                                <div className={`w-14 h-14 rounded-xl bg-neutral-950/60 border ${step.border} flex items-center justify-center`}>
                                    <step.icon className={`w-6 h-6 ${step.color}`} />
                                </div>
                            </div>
                            <div className="flex-1">
                                <div className="flex items-center gap-3 mb-2">
                                    <span className={`text-xs font-mono font-bold ${step.color}`}>{step.number}</span>
                                    <h3 className="text-xl font-display font-semibold dark:text-white text-neutral-900">{step.title}</h3>
                                </div>
                                <p className="text-sm dark:text-neutral-400 text-neutral-500 leading-relaxed max-w-xl">{step.description}</p>
                            </div>
                            {i < steps.length - 1 && (
                                <div className="hidden md:flex items-center absolute -bottom-6 left-12 z-10">
                                    <div className="w-px h-6 bg-neutral-700/50" />
                                </div>
                            )}
                        </motion.div>
                    ))}
                </motion.div>

                {/* CTA */}
                <motion.div
                    variants={fadeIn}
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true }}
                    className="text-center"
                >
                    <p className="dark:text-neutral-400 text-neutral-500 mb-6">Ready to generate your first research idea?</p>
                    <Link
                        to="/register"
                        className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl dark:text-white text-neutral-900 font-semibold transition-all hover:scale-[1.02]"
                        style={{
                            background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%)',
                        }}
                    >
                        Get Started <ArrowRight className="w-4 h-4" />
                    </Link>
                </motion.div>
            </div>
        </div>
    );
};

export default HowItWorksPage;
