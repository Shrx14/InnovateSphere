import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import { User, Lock, Save } from 'lucide-react';

import api from '@/lib/api';
import { fadeIn, staggerContainer } from '@/lib/motion';

import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

export default function UserProfilePage() {
    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [domains, setDomains] = useState([]);

    // Editable fields
    const [username, setUsername] = useState('');
    const [skillLevel, setSkillLevel] = useState('beginner');
    const [preferredDomainId, setPreferredDomainId] = useState('');

    // Password change
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [changingPassword, setChangingPassword] = useState(false);

    useEffect(() => {
        Promise.all([
            api.get('/user/profile'),
            api.get('/domains').catch(() => ({ data: { domains: [] } })),
        ]).then(([profileRes, domainsRes]) => {
            const p = profileRes.data;
            setProfile(p);
            setUsername(p.username || '');
            setSkillLevel(p.skill_level || 'beginner');
            setPreferredDomainId(p.preferred_domain_id || '');
            setDomains(domainsRes.data.domains || []);
            setLoading(false);
        }).catch(() => setLoading(false));
    }, []);

    const handleSave = async () => {
        setSaving(true);
        try {
            const res = await api.put('/user/profile', {
                username,
                skill_level: skillLevel,
                preferred_domain_id: preferredDomainId || null,
            });
            toast.success('Profile updated successfully');
            setProfile(prev => ({ ...prev, ...res.data.user }));
        } catch (err) {
            toast.error(err.response?.data?.error || 'Failed to update profile');
        } finally {
            setSaving(false);
        }
    };

    const handlePasswordChange = async () => {
        if (!currentPassword || !newPassword) {
            toast.error('Please fill in both password fields');
            return;
        }
        setChangingPassword(true);
        try {
            await api.put('/user/password', {
                current_password: currentPassword,
                new_password: newPassword,
            });
            toast.success('Password changed successfully');
            setCurrentPassword('');
            setNewPassword('');
        } catch (err) {
            toast.error(err.response?.data?.error || 'Failed to change password');
        } finally {
            setChangingPassword(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-neutral-950/0">
                <div className="max-w-2xl mx-auto px-6 py-12 md:py-20">
                    <div className="h-10 w-48 bg-neutral-800 rounded-lg mb-8" />
                    <div className="h-64 bg-neutral-800 rounded-2xl" />
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-neutral-950/0">
            <div className="max-w-2xl mx-auto px-6 py-12 md:py-20">
                <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-8">

                    <motion.div variants={fadeIn}>
                        <h1 className="text-4xl md:text-5xl font-light text-white mb-2">Profile</h1>
                        <p className="text-neutral-400">Manage your account settings</p>
                    </motion.div>

                    {/* Profile Info */}
                    <motion.div variants={fadeIn}>
                        <Card className="p-8">
                            <div className="flex items-center gap-3 mb-6">
                                <User className="w-5 h-5 text-indigo-400" />
                                <h2 className="text-sm font-semibold text-indigo-400 uppercase tracking-widest">Account Details</h2>
                            </div>

                            <div className="space-y-5">
                                <div>
                                    <label className="block text-sm font-medium text-neutral-300 mb-2">Email</label>
                                    <input
                                        type="email"
                                        value={profile?.email || ''}
                                        disabled
                                        className="w-full h-10 rounded-lg border border-neutral-700 bg-neutral-800/50 px-3 text-sm text-neutral-400 cursor-not-allowed"
                                    />
                                    <p className="text-xs text-neutral-600 mt-1">Email cannot be changed</p>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-neutral-300 mb-2">Username</label>
                                    <input
                                        type="text"
                                        value={username}
                                        onChange={e => setUsername(e.target.value)}
                                        className="w-full h-10 rounded-lg border border-neutral-700 bg-neutral-800 px-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-neutral-300 mb-2">Skill Level</label>
                                    <select
                                        value={skillLevel}
                                        onChange={e => setSkillLevel(e.target.value)}
                                        className="w-full h-10 rounded-lg border border-neutral-700 bg-neutral-800 px-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                    >
                                        <option value="beginner">Beginner</option>
                                        <option value="intermediate">Intermediate</option>
                                        <option value="advanced">Advanced</option>
                                        <option value="expert">Expert</option>
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-neutral-300 mb-2">Preferred Domain</label>
                                    <select
                                        value={preferredDomainId}
                                        onChange={e => setPreferredDomainId(e.target.value)}
                                        className="w-full h-10 rounded-lg border border-neutral-700 bg-neutral-800 px-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                    >
                                        <option value="">No preference</option>
                                        {domains.map(d => (
                                            <option key={d.id} value={d.id}>{d.name}</option>
                                        ))}
                                    </select>
                                </div>

                                <Button onClick={handleSave} disabled={saving} className="w-full">
                                    <Save className="w-4 h-4 mr-2" />
                                    {saving ? 'Saving...' : 'Save Changes'}
                                </Button>
                            </div>
                        </Card>
                    </motion.div>

                    {/* Password Change */}
                    <motion.div variants={fadeIn}>
                        <Card className="p-8">
                            <div className="flex items-center gap-3 mb-6">
                                <Lock className="w-5 h-5 text-yellow-400" />
                                <h2 className="text-sm font-semibold text-yellow-400 uppercase tracking-widest">Change Password</h2>
                            </div>

                            <div className="space-y-5">
                                <div>
                                    <label className="block text-sm font-medium text-neutral-300 mb-2">Current Password</label>
                                    <input
                                        type="password"
                                        value={currentPassword}
                                        onChange={e => setCurrentPassword(e.target.value)}
                                        className="w-full h-10 rounded-lg border border-neutral-700 bg-neutral-800 px-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-neutral-300 mb-2">New Password</label>
                                    <input
                                        type="password"
                                        value={newPassword}
                                        onChange={e => setNewPassword(e.target.value)}
                                        placeholder="Minimum 6 characters"
                                        className="w-full h-10 rounded-lg border border-neutral-700 bg-neutral-800 px-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                    />
                                </div>

                                <Button
                                    onClick={handlePasswordChange}
                                    disabled={changingPassword || !currentPassword || !newPassword}
                                    variant="secondary"
                                    className="w-full"
                                >
                                    {changingPassword ? 'Changing...' : 'Change Password'}
                                </Button>
                            </div>
                        </Card>
                    </motion.div>

                    {/* Account Info */}
                    <motion.div variants={fadeIn}>
                        <Card className="p-6">
                            <p className="text-sm text-neutral-500">
                                Member since {profile?.created_at ? new Date(profile.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }) : 'Unknown'}
                            </p>
                        </Card>
                    </motion.div>

                </motion.div>
            </div>
        </div>
    );
}
