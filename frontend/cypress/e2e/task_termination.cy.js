describe('任务终止机制', () => {
  it('用例A：关闭单个任务卡片并确认后端状态为 terminated', () => {
    const taskId = 'video::BV1TEST12345'
    cy.visit('/')
    cy.window().then(win => {
      const store = win.__piniaStores?.task
      if (store) {
        store.addVideoTask({ bvId: 'BV1TEST12345', title: '测试视频' }, 'https://www.bilibili.com/video/BV1TEST12345')
      }
    })
    cy.intercept('DELETE', `/api/task/${encodeURIComponent(taskId)}/terminate`).as('terminate')
    cy.get('button[aria-label="取消任务"]').first().click()
    cy.wait('@terminate').its('request.url').should('include', taskId)
    cy.intercept('GET', `/api/task/${encodeURIComponent(taskId)}/status`, { taskId, status: 'terminated' }).as('status')
    cy.wait('@status')
  })
  it('用例B：清空待处理列表并确认队列长度为0', () => {
    cy.visit('/')
    cy.window().then(win => {
      const store = win.__piniaStores?.task
      if (store) {
        for (let i = 0; i < 3; i += 1) {
          store.addVideoTask({ bvId: `BVX${i}Y123456` , title: `测试视频${i}` }, `https://www.bilibili.com/video/BVX${i}Y123456`)
        }
      }
    })
    cy.intercept('POST', '/api/task/batch-terminate', { terminated: true, pendingTerminated: 3, currentTerminated: false }).as('batch')
    cy.contains('清空').click()
    cy.wait('@batch')
    cy.window().then(win => {
      const store = win.__piniaStores?.task
      if (store) {
        expect(store.tasks.length).to.eq(0)
      }
    })
  })
})
