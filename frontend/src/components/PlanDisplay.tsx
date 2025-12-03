import type { PlanTask } from '../types'

interface PlanDisplayProps {
    plan: PlanTask[] | null
}

export function PlanDisplay({ plan }: PlanDisplayProps) {
    if (!plan) return null

    return (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h3 className="text-xl font-bold mb-4">Research Plan</h3>

            <div className="space-y-3">
                {plan.map((task) => (
                    <div
                        key={task.task_number}
                        className="flex items-start gap-3 p-3 border border-gray-200 rounded"
                    >
                        <div className="flex-shrink-0 pt-1">
                            {task.status === 'complete' && (
                                <span className="text-green-600 text-xl">✓</span>
                            )}
                            {task.status === 'in_progress' && (
                                <span className="text-blue-600 text-xl">⏳</span>
                            )}
                            {task.status === 'pending' && (
                                <span className="text-gray-400 text-xl">○</span>
                            )}
                            {task.status === 'error' && (
                                <span className="text-red-600 text-xl">✗</span>
                            )}
                        </div>

                        <div className="flex-1">
                            <div className="font-medium">
                                Task {task.task_number}: {task.description}
                            </div>
                            {task.result && (
                                <div className="mt-2 text-sm text-gray-600">
                                    {task.result}
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}
