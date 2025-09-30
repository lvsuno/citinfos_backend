import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    FiCheckCircle,
    FiX,
    FiExternalLink,
    FiUser,
    FiUsers,
    FiFileText,
    FiMessageSquare,
    FiAward,
    FiTool,
    FiArrowLeft,
    FiLoader,
    FiAlertCircle
} from 'react-icons/fi';
import notificationsAPI from '../services/notificationsAPI';
import ModeratorNominationContent from './ModeratorNominationContent';

const NotificationDetail = () => {
    const { notificationId } = useParams();
    const navigate = useNavigate();
    const [notification, setNotification] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [actionLoading, setActionLoading] = useState(false);
    const [showConfirmDialog, setShowConfirmDialog] = useState(false);
    const [pendingAction, setPendingAction] = useState(null);

    useEffect(() => {
        fetchNotificationDetails();
    }, [notificationId]);

    const fetchNotificationDetails = async () => {
        try {
            setLoading(true);
            const data = await notificationsAPI.getNotificationDetail(notificationId);
            setNotification(data);
        } catch (err) {
            console.error('Error fetching notification details:', err);
            setError('Failed to load notification details');
        } finally {
            setLoading(false);
        }
    };

    const handleModeratorNomination = async (action) => {
        if (!notification?.content_object?.id) return;

        try {
            setActionLoading(true);
            const response = await notificationsAPI.processModeratorNomination({
                membership_id: notification.content_object.id,
                action: action
            });

            // Show success message and refresh
            setNotification(prev => ({
                ...prev,
                content_object: {
                    ...prev.content_object,
                    status: action === 'accept' ? 'accepted' : 'declined',
                    can_respond: false
                }
            }));

            // Close dialog
            setShowConfirmDialog(false);
            setPendingAction(null);

        } catch (err) {
            console.error('Error processing moderator nomination:', err);
            setError('Failed to process nomination');
        } finally {
            setActionLoading(false);
        }
    };

    const confirmAction = (action) => {
        setPendingAction(action);
        setShowConfirmDialog(true);
    };

    const getContentIcon = (contentType) => {
        switch (contentType) {
            case 'post': return <FiFileText className="w-5 h-5" />;
            case 'comment': return <FiMessageSquare className="w-5 h-5" />;
            case 'message': return <FiMessageSquare className="w-5 h-5" />;
            case 'community_role_membership': return <FiUsers className="w-5 h-5" />;
            case 'community': return <FiUsers className="w-5 h-5" />;
            case 'user_profile': return <FiUser className="w-5 h-5" />;
            case 'badge': return <FiAward className="w-5 h-5" />;
            case 'equipment': return <FiTool className="w-5 h-5" />;
            default: return <FiExternalLink className="w-5 h-5" />;
        }
    };

    const getPriorityColor = (priority) => {
        switch (priority) {
            case 1: return 'bg-red-100 text-red-800 border-red-200';
            case 2: return 'bg-orange-100 text-orange-800 border-orange-200';
            case 3: return 'bg-blue-100 text-blue-800 border-blue-200';
            case 4: return 'bg-green-100 text-green-800 border-green-200';
            case 5: return 'bg-gray-100 text-gray-800 border-gray-200';
            default: return 'bg-blue-100 text-blue-800 border-blue-200';
        }
    };

    const getPriorityLabel = (priority) => {
        switch (priority) {
            case 1: return 'High';
            case 2: return 'Elevated';
            case 3: return 'Normal';
            case 4: return 'Low';
            case 5: return 'Very Low';
            default: return 'Normal';
        }
    };

    const formatDateTime = (dateString) => {
        return new Date(dateString).toLocaleString();
    };

    const renderContentObject = () => {
        if (!notification.content_object) {
            return (
                <div className="text-gray-500 text-sm">
                    No content details available
                </div>
            );
        }

        const content = notification.content_object;

        switch (content.type) {
            case 'post':
                return (
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mt-4">
                        <h3 className="text-lg font-semibold mb-2">
                            Post: {content.title}
                        </h3>
                        <p className="text-gray-600 mb-3">
                            {content.content_preview}
                        </p>
                        <div className="text-sm text-gray-500">
                            By {content.author} • {formatDateTime(content.created_at)}
                        </div>
                        {content.community && (
                            <span className="inline-block mt-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                                {content.community.name}
                            </span>
                        )}
                    </div>
                );

            case 'comment':
                return (
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mt-4">
                        <h3 className="text-lg font-semibold mb-2">
                            Comment
                        </h3>
                        <p className="text-gray-600 mb-3">
                            {content.content_preview}
                        </p>
                        <div className="text-sm text-gray-500">
                            By {content.author} • {formatDateTime(content.created_at)}
                        </div>
                        {content.post && (
                            <div className="text-sm text-gray-500 mt-1">
                                On post: {content.post.title}
                            </div>
                        )}
                    </div>
                );

            case 'community_role_membership':
                return (
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mt-4">
                        <h3 className="text-lg font-semibold mb-4">
                            Moderator Nomination
                        </h3>

                        {content.community && (
                            <div className="mb-4">
                                <h4 className="text-base font-medium mb-1">
                                    {content.community.name}
                                </h4>
                                <p className="text-gray-600 text-sm mb-2">
                                    {content.community.description}
                                </p>
                                <div className="text-xs text-gray-500">
                                    {content.community.member_count} members
                                </div>
                            </div>
                        )}

                        <div className="space-y-2 text-sm">
                            <div>
                                <strong>Role:</strong> {content.role}
                            </div>

                            {content.assigned_by && (
                                <div>
                                    <strong>Assigned by:</strong> {content.assigned_by.name}
                                </div>
                            )}

                            <div className="flex items-center space-x-2">
                                <strong>Status:</strong>
                                <span className={`px-2 py-1 text-xs rounded-full ${
                                    content.status === 'accepted' ? 'bg-green-100 text-green-800' :
                                    content.status === 'declined' ? 'bg-red-100 text-red-800' :
                                    'bg-yellow-100 text-yellow-800'
                                }`}>
                                    {content.status}
                                </span>
                            </div>
                        </div>

                        {content.status === 'pending' && (
                            <div className="flex space-x-3 mt-4">
                                <button
                                    onClick={() => confirmAction('accept')}
                                    disabled={actionLoading}
                                    className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <FiCheckCircle className="w-4 h-4" />
                                    <span>Accept Role</span>
                                </button>
                                <button
                                    onClick={() => confirmAction('decline')}
                                    disabled={actionLoading}
                                    className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <FiX className="w-4 h-4" />
                                    <span>Decline Role</span>
                                </button>
                            </div>
                        )}
                    </div>
                );

            case 'community':
                return (
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mt-4">
                        <h3 className="text-lg font-semibold mb-2">
                            Community: {content.name}
                        </h3>
                        <p className="text-gray-600 mb-3">
                            {content.description}
                        </p>
                        <div className="text-sm text-gray-500">
                            {content.member_count} members • Created {formatDateTime(content.created_at)}
                        </div>
                    </div>
                );

            case 'user_profile':
                return (
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mt-4">
                        <div className="flex items-center space-x-3 mb-3">
                            <div className="w-12 h-12 bg-gray-300 rounded-full flex items-center justify-center">
                                <FiUser className="w-6 h-6 text-gray-600" />
                            </div>
                            <div>
                                <h3 className="text-lg font-semibold">
                                    {content.display_name || content.username}
                                </h3>
                                <div className="text-sm text-gray-500">
                                    @{content.username}
                                </div>
                            </div>
                        </div>
                        {content.bio && (
                            <p className="text-gray-600 mb-2">
                                {content.bio}
                            </p>
                        )}
                        <div className="text-sm text-gray-500">
                            Joined {formatDateTime(content.joined_at)}
                        </div>
                    </div>
                );

            default:
                return (
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mt-4">
                        <div className="text-sm text-gray-600">
                            Content type: {content.type}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                            ID: {content.id}
                        </div>
                    </div>
                );
        }
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center p-8">
                <FiLoader className="w-8 h-8 animate-spin text-blue-600" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="max-w-4xl mx-auto p-6">
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                    <div className="flex items-center space-x-2">
                        <FiAlertCircle className="w-5 h-5 text-red-500" />
                        <span className="text-red-800">{error}</span>
                    </div>
                </div>
                <button
                    onClick={() => navigate('/notifications')}
                    className="flex items-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                >
                    <FiArrowLeft className="w-4 h-4" />
                    <span>Back to Notifications</span>
                </button>
            </div>
        );
    }

    if (!notification) {
        return (
            <div className="max-w-4xl mx-auto p-6">
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                    <div className="flex items-center space-x-2">
                        <FiAlertCircle className="w-5 h-5 text-yellow-500" />
                        <span className="text-yellow-800">Notification not found</span>
                    </div>
                </div>
                <button
                    onClick={() => navigate('/notifications')}
                    className="flex items-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                >
                    <FiArrowLeft className="w-4 h-4" />
                    <span>Back to Notifications</span>
                </button>
            </div>
        );
    }

    // Special handling for community role change notifications
    if (notification && notification.notification_type === 'community_role_change') {
        return (
            <ModeratorNominationContent
                notificationId={notification.id}
                showBackButton={true}
                onBack={() => navigate('/notifications')}
                onComplete={(action, response) => {
                    // Refresh notification data after action
                    fetchNotificationDetails();
                }}
            />
        );
    }

    return (
        <div className="max-w-4xl mx-auto p-6">
            <div className="bg-white rounded-lg shadow-sm border">
                <div className="p-6">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center space-x-3">
                            {getContentIcon(notification.content_type_name)}
                            <h1 className="text-2xl font-bold text-gray-900">
                                {notification.title}
                            </h1>
                        </div>
                        <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getPriorityColor(notification.priority)}`}>
                            {getPriorityLabel(notification.priority)}
                        </span>
                    </div>

                    {/* Sender info */}
                    {notification.sender_name && (
                        <div className="flex items-center space-x-3 mb-4">
                            <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
                                <FiUser className="w-4 h-4 text-gray-600" />
                            </div>
                            <span className="text-gray-700">
                                From: {notification.sender_display_name || notification.sender_name}
                            </span>
                        </div>
                    )}

                    {/* Message */}
                    <p className="text-gray-800 text-lg mb-6">
                        {notification.message}
                    </p>

                    {/* Metadata */}
                    <div className="flex flex-wrap gap-4 mb-6 text-sm text-gray-500">
                        <span>{notification.time_ago} ago</span>
                        <span>Type: {notification.notification_type}</span>
                        {notification.is_read && (
                            <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">
                                Read
                            </span>
                        )}
                    </div>

                    <div className="border-t border-gray-200 pt-6">
                        {/* Content Object */}
                        <h2 className="text-lg font-semibold text-gray-900 mb-4">
                            Related Content
                        </h2>
                        {renderContentObject()}

                        {/* Action URL */}
                        {notification.action_url && (
                            <div className="mt-6">
                                <button
                                    onClick={() => navigate(notification.action_url)}
                                    className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                                >
                                    <FiExternalLink className="w-4 h-4" />
                                    <span>View Content</span>
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Back button */}
            <button
                onClick={() => navigate('/notifications')}
                className="mt-6 flex items-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
            >
                <FiArrowLeft className="w-4 h-4" />
                <span>Back to Notifications</span>
            </button>

            {/* Confirmation Dialog */}
            {showConfirmDialog && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
                        <div className="p-6">
                            <h3 className="text-lg font-semibold text-gray-900 mb-4">
                                Confirm {pendingAction === 'accept' ? 'Accept' : 'Decline'} Moderator Role
                            </h3>
                            <p className="text-gray-600 mb-4">
                                Are you sure you want to {pendingAction} the moderator role for{' '}
                                {notification?.content_object?.community?.name}?
                            </p>
                            {pendingAction === 'accept' && (
                                <p className="text-sm text-gray-500 mb-6">
                                    As a moderator, you'll be responsible for maintaining community guidelines
                                    and helping create a positive environment for all members.
                                </p>
                            )}

                            <div className="flex space-x-3">
                                <button
                                    onClick={() => setShowConfirmDialog(false)}
                                    disabled={actionLoading}
                                    className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={() => handleModeratorNomination(pendingAction)}
                                    disabled={actionLoading}
                                    className={`flex-1 px-4 py-2 text-white rounded-lg disabled:opacity-50 ${
                                        pendingAction === 'accept'
                                            ? 'bg-green-600 hover:bg-green-700'
                                            : 'bg-red-600 hover:bg-red-700'
                                    }`}
                                >
                                    {actionLoading ? (
                                        <FiLoader className="w-4 h-4 animate-spin mx-auto" />
                                    ) : (
                                        pendingAction === 'accept' ? 'Accept' : 'Decline'
                                    )}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default NotificationDetail;
